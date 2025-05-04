"""Runtime context for dependency injection.

Use with create_agent's context_schema for passing request-scoped data.

Context is accessed in:
- Tools: runtime.context.user_id
- Middleware: request.runtime.context.user_id
- Before/after hooks: runtime.context.user_id
"""

from dataclasses import dataclass, field


@dataclass
class RequestContext:
    """Context passed to agents at runtime.

    Add fields here for data that should be accessible
    in middleware and tools during agent execution.

    Example usage in tools:
        @tool
        def my_tool(runtime: ToolRuntime[RequestContext]) -> str:
            user_id = runtime.context.user_id
            return f"Hello {user_id}"

    Example usage in middleware:
        @wrap_model_call
        def my_middleware(request: ModelRequest, handler):
            user_id = request.runtime.context.user_id
            ...
    """

    user_id: str = ""
    session_id: str = ""
    user_role: str = "user"  # For permission-based tool filtering
    metadata: dict = field(default_factory=dict)
