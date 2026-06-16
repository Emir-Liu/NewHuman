"""
业务办理回复节点
当用户意图为"业务办理"且识别到具体业务、情绪非 angry 时，返回固定引导话术
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

BUSINESS_REPLY_TEXT = "为您找到相关菜单，请您选择要办理的业务"


async def business_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    业务办理固定回复节点（非 angry 情绪）
    """
    writer = create_event_writer(state, node_name="business_reply")

    response_text = BUSINESS_REPLY_TEXT
    writer.send_token(delta=response_text, full_text=response_text, state=state)
    writer.send_message_end(state=state)

    new_state = {
        "current_response": response_text,
        "inquiry_response_tts": response_text,
        "inquiry_response_display": response_text,
        "response": response_text,
        "bool_ai_generate": False,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
