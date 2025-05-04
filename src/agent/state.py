"""State and output schemas.

LangChain v1 requires TypedDict for state schemas.
Extend langchain.agents.AgentState to add custom fields.
"""

from langchain.agents import AgentState
from pydantic import BaseModel, Field


class Output(BaseModel):
    """Structured output from agents.

    Populated in state["structured_response"] when using
    response_format in create_agent.
    """

    answer: str = Field(description="The response to the user")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence 0-1")
    sources: list[str] = Field(default_factory=list, description="Sources or tools used")


class State(AgentState):
    """Custom state extending AgentState.

    AgentState already includes:
        messages: Annotated[list[AnyMessage], add_messages]

    Add custom fields here. Access in tools via runtime.state["field_name"].
    """

    node: str
    """Which node to execute (for routing)."""
