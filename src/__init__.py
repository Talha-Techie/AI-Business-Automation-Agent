"""LangGraph Agent Template.

A scalable, generic template for building LangGraph agents.

Quick Start:
    from src import graph, NODES

    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "Hello"}], "node": "assistant"},
        {"configurable": {"thread_id": "123"}}
    )

Adding a new agent:
    1. Add node name to src/core/constants.py NODES list
    2. Create agent factory in src/agent/agents.py
    3. Create node method in src/agent/nodes.py Nodes class
"""

from src.agent import NODES, Output, State, build_graph, compile_graph, graph
from src.core import DEFAULT_MIDDLEWARE, RequestContext, logger, settings

__all__ = [
    "DEFAULT_MIDDLEWARE",
    "NODES",
    "Output",
    "RequestContext",
    "State",
    "build_graph",
    "compile_graph",
    "graph",
    "logger",
    "settings",
]
