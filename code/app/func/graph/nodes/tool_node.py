"""LangGraph 工具执行节点。"""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import AIMessage, ToolMessage

from func.graph.state.state import WorkflowState
from func.graph.tools.tool_registry import invoke_tool_async


def _tool_call_fields(tc) -> tuple[str, dict, str]:
    if isinstance(tc, dict):
        name = tc.get("name") or ""
        args = tc.get("args") or {}
        tid = tc.get("id") or str(uuid.uuid4())
    else:
        name = getattr(tc, "name", "") or ""
        args = getattr(tc, "args", None) or {}
        tid = getattr(tc, "id", None) or str(uuid.uuid4())
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    return name, args, tid


async def tool_node(state: WorkflowState) -> dict:
    from langgraph.config import get_stream_writer

    writer = get_stream_writer()
    messages = state.get("messages") or []
    if not messages:
        return {"messages": []}

    last = messages[-1]
    if not isinstance(last, AIMessage):
        return {"messages": []}

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return {"messages": []}

    outputs: list[ToolMessage] = []
    for tc in tool_calls:
        name, args, tid = _tool_call_fields(tc)
        if not name:
            continue
        content = await invoke_tool_async(name, args)
        max_len = 8000
        display_result = (
            content
            if len(content) <= max_len
            else content[:max_len] + "\n...(truncated)"
        )
        writer({
            "type": "tool_call",
            "tool": name,
            "args": args,
            "result": display_result,
        })
        outputs.append(ToolMessage(content=content, tool_call_id=tid, name=name))

    return {"messages": outputs}
