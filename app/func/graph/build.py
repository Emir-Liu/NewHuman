from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from func.graph.state import MessagesState
from func.graph.nodes.llm_call_node import llm_call
from func.graph.nodes.tool_node import tool_node
from func.graph.edges.should_continue import should_continue


def build_graph():

    agent_builder = StateGraph(MessagesState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", END]
    )
    agent_builder.add_edge("tool_node", "llm_call")

    checkpointer = MemorySaver()

    # Compile the agent
    agent = agent_builder.compile(checkpointer=checkpointer)

    return agent