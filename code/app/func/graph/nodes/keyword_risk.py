"""
金融风险检测-关键词
遍历 risk_keyword_list，检测用户 query 中是否包含风险关键词
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer


async def keyword_risk_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    金融风险关键词检测节点
    """
    writer = create_event_writer(state, node_name="keyword_risk")

    messages = state.get("messages", [])
    query = state.get("query", "")

    risk_keyword_list = state.get("risk_keyword_list", [])
    bool_risk = 0

    for risk_keyword in risk_keyword_list:
        if risk_keyword in query:
            bool_risk = 1
            break

    new_state = {
        "bool_risk": bool_risk,
        # "query": query,
    }

    if bool_risk == 1:
        new_state.update(
            {
                "business":[],
                "business_status":"sensitive_word",
                "emotion":"neutral"
            }
        )

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
