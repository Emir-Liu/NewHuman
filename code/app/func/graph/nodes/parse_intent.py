"""
意图解析节点
将意图识别 LLM 的输出进行后处理，写入 conversation 变量
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer


async def parse_intent_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    意图解析后处理节点
    确保意图识别结果的字段完整性
    """
    writer = create_event_writer(state, node_name="parse_intent")

    emotion = state.get("emotion", "neutral")
    business_status = state.get("business_status", "reject")
    business = state.get("business", [])

    # 确保字段存在
    new_state = {
        "emotion": emotion,
        "business_status": business_status,
        "business": business
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
