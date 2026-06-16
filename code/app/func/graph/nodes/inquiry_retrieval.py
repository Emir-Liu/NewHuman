"""
咨询 QA 知识库检索节点
在意图识别为咨询后，使用 rewrite 检索咨询专用 QA 知识库（chunk_mode=qa，Q 匹配、A 作答）
"""

from typing import Any, AsyncIterator, Dict, List

from func.graph.state.state import WorkflowState
from func.graph.writer.writer import create_event_writer
from func.graph.utils.knowledge_format import format_knowledge_result
from func.kb_system_langchain.factories import KBManagerFactory

_kb_manager = KBManagerFactory.create("default")


async def inquiry_retrieval_node(state: WorkflowState) -> AsyncIterator[Dict[str, Any]]:
    """
    咨询 QA 知识库检索节点

    优先使用 state.rewrite 作为检索 query；
    必须配置 inquiry_kb_id（咨询专用 QA 库），未配置时回退 label=inquiry。
    """
    writer = create_event_writer(state, node_name="inquiry_retrieval")

    query = state.get("rewrite") or state.get("query", "")
    inquiry_kb_id = state.get("inquiry_kb_id", "")
    inquiry_kb_top_k = state.get("inquiry_kb_top_k", 5)

    records: List[Dict[str, Any]] = []
    try:
        if inquiry_kb_id:
            result = _kb_manager.search(
                kb_id=inquiry_kb_id,
                query=query,
                top_k=inquiry_kb_top_k,
            )
        else:
            result = _kb_manager.search_by_label(
                query=query,
                label="inquiry",
                top_k=inquiry_kb_top_k,
            )
        records = result.get("records", [])
    except Exception:
        records = []

    inquiry_knowledge_result = format_knowledge_result(records)

    new_state = {
        "inquiry_rag_result": records,
        "inquiry_knowledge_result": inquiry_knowledge_result,
        "knowledge_result": inquiry_knowledge_result,
    }

    writer.send_node_end(updates=new_state, state={**state, **new_state})
    return new_state
