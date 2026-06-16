"""
拒识固定回复节点
当用户输入无实质业务指向时，返回引导话术
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

REJECT_REPLY_TEXT = "您好，请说您要办理的业务"


async def reject_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    拒识回复节点
    返回引导用户描述业务的固定话术
    """
    writer = create_event_writer(state, node_name="reject_reply")

    full_response = REJECT_REPLY_TEXT
    writer.send_token(delta=full_response, full_text=full_response, state=state)
    writer.send_message_end(state=state)

    new_state = {
        "current_response": full_response,
        "inquiry_response_tts": full_response,
        "inquiry_response_display": full_response,
        "response": full_response,
        "bool_ai_generate": False,
    }

    return new_state
