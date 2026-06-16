"""
防注入关键词检测
遍历 injection_keyword_list，若用户 query 中包含防注入关键词则标记 bool_injection=1
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer


async def injection_check_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    防注入关键词检测节点
    """
    writer = create_event_writer(state, node_name="injection_check")

    messages = state.get("messages", [])
    query = state.get("query", "")

    injection_keyword_list = state.get("injection_keyword_list", [])
    bool_injection = 0

    for keyword in injection_keyword_list:
        if keyword in query:
            bool_injection = 1
            break

    new_state = {
        "bool_injection": bool_injection,
    }

    if bool_injection == 1:
        new_state.update(
            {
                "business":[],
                "business_status":"anti_injection",
                "emotion":"neutral"
            }
        )

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
