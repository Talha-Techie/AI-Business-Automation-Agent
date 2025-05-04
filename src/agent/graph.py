"""LangGraph workflow builder.

Builds a graph where:
- START routes to the requested node based on state["node"]
- Each node executes its agent and ends
- Subgraphs can be added as nodes for complex workflows

Features:
- Checkpointer: Short-term memory (conversation history per thread)
- Store: Long-term memory (persisted across threads/sessions)
- Subgraph support: Add compiled subgraphs as nodes
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from src.agent.nodes import nodes
from src.agent.state import State
from src.core.constants import NODES


def route_to_node(state: State) -> str:
    """Route to the requested node based on state['node']."""
    return state.get("node", "assistant")


def build_graph() -> StateGraph:
    """Build the agent graph.

    Returns:
        Uncompiled StateGraph ready for customization or compilation.
    """
    graph = StateGraph(State)

    # Register all nodes - method name must match node name
    for node_name in NODES:
        graph.add_node(node_name, getattr(nodes, node_name))

    # Route from START to requested node
    graph.add_conditional_edges(START, route_to_node, {n: n for n in NODES})

    # All nodes end after execution (modify for multi-step workflows)
    for node_name in NODES:
        graph.add_edge(node_name, END)

    return graph


def compile_graph(
    checkpointer=None,
    store=None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
):
    """Compile the graph with persistence and optional interrupts.

    Args:
        checkpointer: Checkpointer for short-term memory. Defaults to MemorySaver.
        store: Store for long-term memory. Defaults to InMemoryStore.
        interrupt_before: Node names to interrupt before (human-in-the-loop).
        interrupt_after: Node names to interrupt after.

    Returns:
        Compiled graph ready for invocation.
    """
    graph = build_graph()
    return graph.compile(
        checkpointer=checkpointer or MemorySaver(),
        store=store or InMemoryStore(),
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
    )


# -----------------------------------------------------------------------------
# Subgraph Support
# -----------------------------------------------------------------------------
# To add a subgraph:
#
# from src.agent.graph import build_graph
#
# # Build your subgraph
# subgraph_builder = StateGraph(SubgraphState)
# subgraph_builder.add_node("sub_node", sub_node_fn)
# subgraph_builder.add_edge(START, "sub_node")
# subgraph = subgraph_builder.compile()
#
# # Add to main graph
# graph = build_graph()
# graph.add_node("my_subgraph", subgraph)
# graph.add_edge("assistant", "my_subgraph")  # Route assistant -> subgraph
# compiled = graph.compile(checkpointer=MemorySaver())


# Default compiled instance
graph = compile_graph()
