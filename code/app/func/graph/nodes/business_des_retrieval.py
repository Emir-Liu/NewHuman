"""
知识库检索节点
在指代消解后，使用 rewrite 文本检索已有知识库，结果写入 state['knowledge_result']
"""

from typing import Any, AsyncIterator, Dict, List

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer
from func.kb_system_langchain.factories import KBManagerFactory

_kb_manager = KBManagerFactory.create("default")


def _format_knowledge_result(records: List[Dict[str, Any]]) -> str:
    """将检索记录格式化为 LLM 可用的 context 文本"""
    if not records:
        return ""

    parts: List[str] = []
    for i, item in enumerate(records, 1):
        segment = item.get("segment", {})
        content = segment.get("content", "")
        score = item.get("score", 0)
        if content:
            parts.append(f"[{i}] (score={score:.3f})\n{content}")
    return "\n\n".join(parts)


async def business_des_retrieval_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    知识库检索节点

    优先使用 state.rewrite 作为检索 query；
    可通过 inputs.kb_id 指定单个知识库，否则按 inputs.kb_label 检索所有启用知识库。
    """
    writer = create_event_writer(state, node_name="business_des_retrieval")

    query = state.get("rewrite") or state.get("query", "")
    rewrite = state.get("rewrite")
    business_des_kb_top_k = state.get("business_des_kb_top_k")
    business_des_kb_id = state.get("business_des_kb_id")

    # kb_id = inputs.get("kb_id")
    # kb_label = inputs.get("kb_label", kb_label_default)
    # top_k = inputs.get("kb_top_k", kb_top_k_default)

    records: List[Dict[str, Any]] = []
    try:
        result = _kb_manager.search(
            kb_id=business_des_kb_id, 
            query=rewrite, 
            top_k=business_des_kb_top_k
        )
        records = result.get("records", [])
    except Exception:
        records = []

    business_des_knowledge_result = _format_knowledge_result(records)

    new_state = {
        "business_des_knowledge_result": business_des_knowledge_result,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
