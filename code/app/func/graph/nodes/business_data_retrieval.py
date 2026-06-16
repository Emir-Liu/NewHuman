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


async def business_data_retrieval_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    业务数据检索节点
    """
    writer = create_event_writer(state, node_name="business_data_retrieval")

    query = state.get("query", "")
    rewrite = state.get("rewrite", query)
    business_data_kb_top_k = state.get("business_data_kb_top_k")
    business_data_kb_id = state.get("business_data_kb_id")

    records: List[Dict[str, Any]] = []
    try:
        result = _kb_manager.search(
            kb_id=business_data_kb_id, 
            query=rewrite, 
            top_k=business_data_kb_top_k
        )
        records = result.get("records", [])
    except Exception:
        records = []

    business_data_knowledge_result = _format_knowledge_result(records)

    new_state = {
        "business_data_knowledge_result": business_data_knowledge_result,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
