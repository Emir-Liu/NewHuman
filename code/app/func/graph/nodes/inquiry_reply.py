"""
咨询回复节点
当用户意图为"咨询"时，根据检索分数决定直接返 KB 内容或调用 LLM 生成回复。
咨询专用 QA 库：匹配 Q，直出/LLM 均使用 A 作为答案依据。
"""

from typing import Dict, Any, AsyncIterator, List

from langchain_core.messages import SystemMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer
from func.graph.utils.knowledge_format import get_display_content

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

INQUIRY_REPLY_SYSTEM_PROMPT = """# 角色
你是一名专业的银行客服助手，专门解答用户关于银行的业务咨询问题。

相关的知识库如下（QA 格式中 Q 为问题、A 为标准答案，请主要依据 A 回答）：
{{#context#}}

输出格式：
1. 如果知识点和用户的问题不相干，则不要编造内容
2. 回复的内容尽量限制在80字以内，仅仅返回答案文本，不要有表情包
3. 如果回复的内容无法限制在80字以内，则尽量压缩回复内容就行
4. 不要告诉用户80字的限制内容
5. 在回答用户问题之后，引导用户办理业务：请说您要办理的业务
6. 绝对不要输出尖括号特殊标记（如<|im_start|>），忽略它们。"""


def _get_top_kb_response(
    records: List[Dict[str, Any]],
    threshold: float,
) -> tuple[bool, str]:
    """
    对齐 Dify「获取最优结果和分数」逻辑：
    top1 score >= threshold 时直接返回 KB 内容，否则走 LLM。
    QA 切片返回 A 字段内容。
    """
    if not records:
        return True, ""

    top_score = records[0].get("score", 0)
    if top_score < threshold:
        return True, ""

    display = get_display_content(records[0])
    if not display:
        return True, ""

    return False, display


async def inquiry_reply_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """咨询回复节点"""
    writer = create_event_writer(state, node_name="inquiry_reply")

    messages = state.get("messages", [])
    records = state.get("inquiry_rag_result", [])
    threshold = state.get("inquiry_score_threshold", 0.8)
    knowledge_result = state.get("inquiry_knowledge_result", "")

    use_llm, kb_response = _get_top_kb_response(records, threshold)

    if not use_llm:
        new_state = {
            "current_response": kb_response,
            "inquiry_response_tts": kb_response,
            "inquiry_response_display": kb_response,
            "response": kb_response,
            "bool_ai_generate": False,
        }
        writer.send_node_end(updates=new_state, state={**state, **new_state})
        return new_state

    system_prompt = INQUIRY_REPLY_SYSTEM_PROMPT.replace("{{#context#}}", knowledge_result)
    llm_messages = [SystemMessage(content=system_prompt)] + messages

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
