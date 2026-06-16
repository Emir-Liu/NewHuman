"""
指代消解 LLM 节点
结合历史对话，将用户输入中的指代、省略、口语表达重写为清晰完整的书面语
"""

import json
from typing import Dict, Any, AsyncIterator

from langchain_core.messages import SystemMessage, HumanMessage

from config.llm_config import LLMConfig
from utils.llm_operator import LLMOperator
from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer

llm_config = LLMConfig()
model = LLMOperator(llm_config).get_llm()

# 指代消解 System Prompt
REWRITE_SYSTEM_PROMPT = """【rewrite】

你是文本重写助手。结合金融领域知识进行同音/近音纠错并结合【历史对话】，将当前用户输入中的指代、省略、口语表达，重写为清晰、完整、可检索的书面语。

规则：
1. 指代消解："它"、"那个"、"这个"、"他" → 替换成真实业务对象
2. 省略补全：历史对话中包含一个产品→当前"我就买一个"→指代我就买一个某某产品
3. 特殊标记识别：当【历史对话】中出现"为您找到相关菜单"、"请您选择要办理的业务"，说明前一轮已识别出业务需求，当前输入的指代应关联到该业务
4. 同音/近音纠错："挂丝" → "挂失"
5. 如无歧义，返回原句。

只输出重写后的文本，不要解释。"""


async def rewrite_query_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    指代消解节点
    结合历史对话，将用户输入重写为指代消解后的完整表述
    结果存入 state['rewrite']
    """
    writer = create_event_writer(state, node_name="rewrite_query")

    messages = state.get("messages", [])
    query = state.get("query", "")

    llm_messages = [
        SystemMessage(content=REWRITE_SYSTEM_PROMPT),
    ] + messages

    # 调用 LLM 获取重写结果
    result = await model.ainvoke(llm_messages)
    full_response = result.content if hasattr(result, "content") else str(result)

    # 尝试解析 structured output JSON
    rewrite_text = full_response.strip()
    try:
        parsed = json.loads(full_response)
        if isinstance(parsed, dict) and "rewrite" in parsed:
            rewrite_text = parsed["rewrite"].strip()
    except (json.JSONDecodeError, TypeError):
        # 非 JSON 输出，直接使用原始文本
        pass

    if not rewrite_text:
        rewrite_text = query  # 兜底：使用原始 query

    new_state = {
        "rewrite": rewrite_text,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
