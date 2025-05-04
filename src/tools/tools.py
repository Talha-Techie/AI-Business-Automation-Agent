"""Tools for agents.

Tools can use ToolRuntime to access:
- runtime.context: Static context (user_id, api_key, etc.)
- runtime.state: Current agent state
- runtime.store: Long-term memory store
- runtime.tool_call_id: Current tool call ID

Tools can return Command to update state.
"""

from datetime import datetime

from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

from src.core.context import RequestContext


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression like '2 + 2' or '10 * 5'."""
    try:
        allowed = set("0123456789+-*/.(). ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"


@tool
def get_user_info(runtime: ToolRuntime[RequestContext]) -> str:
    """Get information about the current user from context.

    Example tool showing how to access runtime context.
    The runtime parameter is hidden from the model.
    """
    user_id = runtime.context.user_id if runtime.context else "anonymous"
    session_id = runtime.context.session_id if runtime.context else "unknown"
    return f"User: {user_id}, Session: {session_id}"


@tool
def save_preference(key: str, value: str, runtime: ToolRuntime[RequestContext]) -> Command:
    """Save a user preference to long-term memory.

    Example tool showing how to use Store and return Command.
    Returns Command to update agent state.
    """
    user_id = runtime.context.user_id if runtime.context else "anonymous"

    # Save to store if available (long-term memory)
    if runtime.store:
        runtime.store.put(("preferences", user_id), key, {"value": value})

    # Return Command to update state (optional)
    return Command(
        update={
            "messages": [
                {
                    "role": "tool",
                    "content": f"Saved preference '{key}' = '{value}' for user {user_id}",
                    "tool_call_id": runtime.tool_call_id,
                }
            ]
        }
    )


# All available tools
TOOLS = [get_current_time, calculate, get_user_info, save_preference]
