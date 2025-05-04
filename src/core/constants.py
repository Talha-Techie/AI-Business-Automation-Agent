"""Constants and configuration.

Centralized location for node names, model configs, and other constants.
To add a new node:
1. Add it to NODES list
2. Create the node function in nodes.py
3. Create the agent factory in agents.py
"""

from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Node Registry
# -----------------------------------------------------------------------------
# Add new node names here. The graph will register all nodes in this list.

NODES: list[str] = [
    "assistant",
    # "researcher",
]


# -----------------------------------------------------------------------------
# Model Configuration
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration with supported model names."""

    gpt_5_2: str = "gpt-5.2"
    gpt_5_mini: str = "gpt-5-mini"
    o4_mini: str = "o4-mini"
    o3: str = "o3"


models = ModelConfig()


# -----------------------------------------------------------------------------
# Middleware Configuration
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class MiddlewareConfig:
    """Middleware configuration."""

    max_retries: int = 3
    retry_base_delay: float = 1.0
    max_retry_delay: float = 10.0


middleware_config = MiddlewareConfig()
