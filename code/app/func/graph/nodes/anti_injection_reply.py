"""
防注入固定回复节点
当检测到用户尝试注入攻击时，返回引导话术
"""

from typing import Dict, Any, AsyncIterator

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

ANTI_INJECTION_REPLY_TEXT = "请您清晰描述要咨询的业务问题，比如可以说开卡，转账。"


async def anti_injection_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    防注入回复节点
    返回安全引导话术
    """
    writer = create_event_writer(state, node_name="anti_injection_reply")

    full_response = ANTI_INJECTION_REPLY_TEXT
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
