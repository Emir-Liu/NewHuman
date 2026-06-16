"""知识库检索结果格式化工具（支持 QA 切片：Q 匹配、A 作答）"""

from typing import Any, Dict, List, Optional

CHUNK_MODE_QA = "qa"


def _meta_value(segment: Dict[str, Any], name: str) -> str:
    for meta in segment.get("chunk_metadata", []):
        if meta.get("name") == name:
            return str(meta.get("value", "")).strip()
    return ""


def get_chunk_mode(segment: Dict[str, Any]) -> str:
    return _meta_value(segment, "chunk_mode")


def get_segment_answer(segment: Dict[str, Any]) -> str:
    return _meta_value(segment, "A")


def is_qa_segment(segment: Dict[str, Any]) -> bool:
    return get_chunk_mode(segment) == CHUNK_MODE_QA


def get_display_content(record: Dict[str, Any]) -> str:
    """
    返回面向用户的展示文本。
    QA 切片优先返回 A；非 QA 返回 content。
    """
    segment = record.get("segment", {})
    if is_qa_segment(segment):
        answer = get_segment_answer(segment)
        if answer:
            return answer
    return segment.get("content", "")


def format_segment_for_context(segment: Dict[str, Any]) -> Optional[str]:
    """单条切片格式化为 LLM context 片段"""
    content = segment.get("content", "")
    if not content:
        return None

    if is_qa_segment(segment):
        answer = get_segment_answer(segment)
        if answer:
            return f"Q: {content}\nA: {answer}"
        return f"Q: {content}"

    return content


def format_knowledge_result(records: List[Dict[str, Any]]) -> str:
    """将检索记录格式化为 LLM 可用的 context 文本"""
    if not records:
        return ""

    parts: List[str] = []
    for i, item in enumerate(records, 1):
        segment = item.get("segment", {})
        body = format_segment_for_context(segment)
        if not body:
            continue
        score = item.get("score", 0)
        parts.append(f"[{i}] (score={score:.3f})\n{body}")
    return "\n\n".join(parts)
