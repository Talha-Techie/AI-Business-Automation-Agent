"""Agent factory using LangChain v1 create_agent.

To add a new agent:
1. Add a new method to the Agents class
2. Configure tools, prompts, and output schema as needed
"""

from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.agent.state import Output, State
from src.core.constants import models
from src.core.context import RequestContext
from src.core.middleware import DEFAULT_MIDDLEWARE
from src.core.settings import logger, settings
from src.tools import TOOLS


def load_prompt(name: str) -> str:
    """Load prompt from prompts directory."""
    path = Path(__file__).parent.parent / "prompts" / f"{name}.md"
    if path.exists():
        return path.read_text()
    logger.warning(f"Prompt not found: {name}.md")
    return ""


def get_llm(model: str | None = None, **kwargs) -> ChatOpenAI:
    """Get configured LLM instance."""
    return ChatOpenAI(
        model=model or models.gpt_5_mini,
        api_key=settings.OPENAI_API_KEY,
        **kwargs,
    )


class Agents:
    """Agent factory.

    Each method returns a configured agent using LangChain v1 create_agent.
    """

    def assistant(self):
        """General assistant with tools and structured output."""
        return create_agent(
            model=get_llm(),
            tools=TOOLS,
            state_schema=State,
            system_prompt=load_prompt("assistant"),
            response_format=Output,
            middleware=DEFAULT_MIDDLEWARE,
            context_schema=RequestContext,
        )


agents = Agents()
