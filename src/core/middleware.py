"""Middleware for LangChain v1 agents.

Middleware provides hooks at each step in agent execution:
- before_agent: Before calling the agent (load memory, validate input)
- before_model: Before each LLM call (update prompts, trim messages)
- wrap_model_call: Around each LLM call (intercept and modify requests/responses)
- wrap_tool_call: Around each tool call (intercept and modify tool execution)
- after_model: After each LLM response (validate output, apply guardrails)
- after_agent: After agent completes (save results, cleanup)

Decorators available:
- @wrap_model_call: Wrap model calls
- @wrap_tool_call: Wrap tool calls
- @dynamic_prompt: Generate dynamic system prompts
- @before_model / @after_model: Node-style hooks

Recommended middleware is exported in DEFAULT_MIDDLEWARE.
"""

import time
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    SummarizationMiddleware,
    after_model,
    before_model,
    dynamic_prompt,
    wrap_model_call,
)
from langchain.agents.middleware.types import ModelResponse
from langchain.messages import ToolMessage
from langgraph.runtime import Runtime

from src.core.constants import middleware_config
from src.core.context import RequestContext
from src.core.settings import logger

# ============================================================================
# Logging Middleware
# ============================================================================


@wrap_model_call
def logging_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Log model requests and responses."""
    start = time.time()

    # Log request (last message)
    if request.state.get("messages"):
        last_msg = request.state["messages"][-1]
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        logger.info(f"[LLM Request] {content[:100]}...")

    response = handler(request)

    # Log response time
    elapsed = time.time() - start
    logger.info(f"[LLM Response] {elapsed:.2f}s")

    return response


# ============================================================================
# Retry Middleware
# ============================================================================


@wrap_model_call
def retry_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Retry failed model calls with exponential backoff."""
    from src.core.settings import settings

    last_error = None

    for attempt in range(settings.MAX_RETRIES):
        try:
            return handler(request)
        except Exception as e:
            last_error = e
            delay = min(
                middleware_config.retry_base_delay * (2**attempt),
                middleware_config.max_retry_delay,
            )
            logger.warning(f"[Retry] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

    logger.error(f"[Retry] All {settings.MAX_RETRIES} attempts failed")
    raise last_error


# ============================================================================
# Tool Error Handling Middleware
# ============================================================================


class ToolErrorMiddleware(AgentMiddleware):
    """Handle tool execution errors gracefully.

    Returns a ToolMessage with error content instead of raising exceptions.
    This allows the agent to recover and try again with corrected inputs.
    """

    def wrap_tool_call(self, request, handler):
        """Sync version for invoke()."""
        return self._handle(request, handler)

    async def awrap_tool_call(self, request, handler):
        """Async version for ainvoke()/astream()."""
        return await self._ahandle(request, handler)

    def _handle(self, request, handler):
        try:
            return handler(request)
        except Exception as e:
            return self._error_message(request, e)

    async def _ahandle(self, request, handler):
        try:
            return await handler(request)
        except Exception as e:
            return self._error_message(request, e)

    def _error_message(self, request, e: Exception) -> ToolMessage:
        tool_name = request.tool_call.get("name", "unknown")
        error_msg = f"Tool error in '{tool_name}': {e}. Please check your input and try again."
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            tool_call_id=request.tool_call["id"],
        )


tool_error_middleware = ToolErrorMiddleware()


# ============================================================================
# Custom State Middleware (example pattern)
# ============================================================================


class CustomStateMiddleware(AgentMiddleware):
    """Example class-based middleware with multiple hooks.

    Use this pattern when you need:
    - Multiple hooks (before_model, after_model, etc.)
    - Custom state fields accessible in hooks
    - Access to runtime context

    Usage:
        agent = create_agent(
            model=llm,
            tools=tools,
            middleware=[CustomStateMiddleware()],
        )
    """

    def before_model(self, state: dict, runtime) -> dict[str, Any] | None:
        """Called before each model invocation.

        Args:
            state: Current agent state
            runtime: Runtime context (store, context, etc.)

        Returns:
            State updates or None
        """
        # Example: Add context from runtime
        # if runtime.context:
        #     return {"user_id": runtime.context.user_id}
        return None

    def after_model(self, state: dict, runtime) -> dict[str, Any] | None:
        """Called after each model invocation.

        Args:
            state: Current agent state
            runtime: Runtime context

        Returns:
            State updates or None
        """
        return None

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Wrap model calls for interception.

        Use request.override() to modify:
        - system_prompt: Change the system message
        - tools: Filter available tools
        - model: Switch to different model

        Example:
            request = request.override(
                system_prompt="New prompt based on state",
                tools=filtered_tools,
            )
            return handler(request)
        """
        return handler(request)


# ============================================================================
# Dynamic Prompt Middleware
# ============================================================================


@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str | None:
    """Generate dynamic system prompt based on context.

    Returns None to use the static system_prompt from create_agent.
    Return a string to override the system prompt dynamically.

    Access available:
    - request.state: Current agent state
    - request.runtime.context: Runtime context (user_id, etc.)
    - request.runtime.store: Long-term memory store
    - request.messages: Shortcut for request.state["messages"]
    """
    # Example: Modify prompt based on conversation length
    message_count = len(request.messages) if request.messages else 0

    if message_count > 10:
        # For long conversations, ask for concise responses
        return None  # Could return modified prompt here

    # Return None to use default system_prompt
    return None


# ============================================================================
# Before/After Model Hooks
# ============================================================================


@before_model
def log_before_model(state: dict, runtime: Runtime[RequestContext]) -> dict[str, Any] | None:
    """Called before each model invocation.

    Use for:
    - Logging/metrics
    - Validating state
    - Injecting data from context/store

    Returns state updates or None.
    """
    user_id = runtime.context.user_id if runtime.context else "anonymous"
    msg_count = len(state.get("messages", []))
    logger.debug(f"[Before Model] User: {user_id}, Messages: {msg_count}")
    return None


@after_model
def log_after_model(state: dict, runtime: Runtime[RequestContext]) -> dict[str, Any] | None:
    """Called after each model response.

    Use for:
    - Logging/metrics
    - Validating output
    - Updating state based on response

    Returns state updates or None.
    """
    logger.debug("[After Model] Response received")
    return None


# ============================================================================
# Default Middleware Stack
# ============================================================================


def build_middleware() -> list:
    """Build middleware stack based on settings.

    Order: summarization -> logging -> retry -> tool_error
    """
    from src.core.constants import models
    from src.core.settings import settings

    middleware = []

    if settings.ENABLE_SUMMARIZATION:
        middleware.append(
            SummarizationMiddleware(
                model=models.gpt_5_mini,
                trigger=("tokens", 8000),
                keep=("messages", 10),
            )
        )

    if settings.ENABLE_LOGGING:
        middleware.append(logging_middleware)

    if settings.ENABLE_RETRY:
        middleware.append(retry_middleware)

    middleware.append(tool_error_middleware)

    return middleware


# Built at import time based on current settings
DEFAULT_MIDDLEWARE = build_middleware()
