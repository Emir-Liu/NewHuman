from typing import Literal
from langgraph.graph import StateGraph, START, END
from func.graph.state import MessagesState

# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    # print(f'should continue条件边状态:\n{state}')
    last_message = state["messages"][-1]

    # If the LLM makes a tool call, then perform an action
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tool_node'

    # Otherwise, we stop (reply to the user)
    return END
