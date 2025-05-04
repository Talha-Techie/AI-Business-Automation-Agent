"""Node implementations for the agent graph.

Each method in the Nodes class is a graph node.
To add a new node:
1. Add the node name to NODES list in constants.py
2. Create the agent factory in agents.py
3. Add a method here with the same name as the node
"""

from langgraph.runtime import Runtime

from src.agent.agents import agents
from src.agent.state import State
from src.core.context import RequestContext
from src.core.settings import logger


class Nodes:
    """Node implementations.

    Each method is a graph node. Method name must match the node name in NODES.
    Nodes can accept: state, config, runtime (in any combination).
    """

    async def assistant(self, state: State, runtime: Runtime[RequestContext]) -> dict:
        """Assistant node - general purpose agent with tools."""
        context = runtime.context or RequestContext()
        logger.info(f"Executing: assistant (user={context.user_id or 'anonymous'})")
        agent = agents.assistant()
        return await agent.ainvoke(state, context=context)


nodes = Nodes()
