"""
保存对话历史节点
将本轮对话追加到 history，并更新 only_history_str
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer
from langchain_core.messages import AIMessage

async def save_history_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    保存对话历史节点
    将当前 query 和 response 追加到历史记录
    """
    writer = create_event_writer(state, node_name="save_history")

    messages = state.get("messages", [])
    query = state.get("query", "")

    response = state.get("response", "")

    history = state.get("history", [])
    num_history = state.get("num_history", 3)

    new_state = {
        "messages": [AIMessage(content=response)],
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
