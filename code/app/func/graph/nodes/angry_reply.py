"""
愤怒安抚 LLM 节点
业务办理且用户情绪为 angry 时，先安抚情绪再引导办理业务（对齐 Dify LLM 2）
"""

from typing import Dict, Any, AsyncIterator

from langchain_core.messages import SystemMessage, HumanMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

ANGRY_REPLY_SYSTEM_PROMPT = """#角色
你是一名银行接待人员，负责对客户对话的回复

当前客户情绪愤怒，请安抚客户情绪，并告诉用户为您找到相关菜单，请您选择要办理的业务

话术维持在50字以内"""


async def angry_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    愤怒安抚回复节点
    安抚用户情绪并引导办理业务
    """
    writer = create_event_writer(state, node_name="angry_reply")

    query = state.get("query", "")

    llm_messages = [
        SystemMessage(content=ANGRY_REPLY_SYSTEM_PROMPT),
        HumanMessage(content=f"用户输入：{query}"),
    ]

    full_response = ""
    async for chunk in model.astream(llm_messages):
        if hasattr(chunk, "content") and chunk.content:
            token = chunk.content
            full_response += token
            writer.send_token(delta=token, full_text=full_response, state=state)

    writer.send_message_end(state=state)

    new_state = {
        "current_response": full_response,
        "inquiry_response_tts": full_response,
        "inquiry_response_display": full_response,
        "response": full_response,
        "bool_ai_generate": True,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
