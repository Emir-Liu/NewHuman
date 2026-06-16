"""
敏感词/金融风险 LLM 回复节点
当检测到用户输入包含金融风险关键词时，调用大模型生成引导话术
"""

from typing import Dict, Any, AsyncIterator

from langchain_core.messages import SystemMessage, HumanMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

# 敏感词/风险回复 System Prompt
SENSITIVE_REPLY_SYSTEM_PROMPT = """# 角色
你是一个温柔和善的银行人员，负责引导用户办理业务。

# 指令
1. 语言风格：温柔和善，亲切的年轻女性，具有银行的专业素质。
2. 回复行为：用户的输入触发了敏感词或风险内容的检测，请礼貌地提醒用户文明交流，不要进行有风险的操作，并引导用户回到正常的银行业务咨询。
3. 返回结果：尽量限制在 30 字以内，两句话即可。
"""


async def sensitive_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    敏感词/风险 LLM 回复节点
    调用大模型生成引导话术，提醒用户文明交流并引导办理业务
    """
    writer = create_event_writer(state, node_name="sensitive_reply")

    query = state.get("query", "")
    messages = state.get("messages", [])

    llm_messages = [
        SystemMessage(content=SENSITIVE_REPLY_SYSTEM_PROMPT),
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

    return new_state
