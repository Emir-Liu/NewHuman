"""ReAct 条件边 — 是否继续调用工具。"""

from langchain_core.messages import AIMessage

from func.graph.state.state import WorkflowState


def should_continue(state: WorkflowState) -> str:
    messages = state.get("messages") or []
    if not messages:
        return "end"
    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"
