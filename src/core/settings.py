"""Application settings."""

import logging
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")


class Settings(BaseSettings):
    """Configuration from environment variables.

    Model names are in constants.py (ModelConfig).
    """

    ENV: Literal["LOCAL", "DEV", "PROD"] = "LOCAL"

    # LLM
    OPENAI_API_KEY: str = Field(..., description="OpenAI API Key")

    # Middleware
    ENABLE_RETRY: bool = Field(default=False, description="Enable retry middleware")
    ENABLE_LOGGING: bool = Field(default=False, description="Enable logging middleware")
    ENABLE_SUMMARIZATION: bool = Field(default=True, description="Enable summarization middleware")
    MAX_RETRIES: int = Field(default=3, description="Max retry attempts")

    # LangSmith (optional)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "langgraph-agent"


settings = Settings()
