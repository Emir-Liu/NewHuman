"""LLM 调用节点 — bind_tools + 流式 custom writer。"""

from __future__ import annotations

import json
import re
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config.llm_config import LLMConfig
from config.agent_config import get_agent_config
from func.graph.state.state import WorkflowState
from func.graph.tools.tool_registry import (
    format_json_tool_call_example,
    format_tools_prompt_names,
    get_allowed_tools,
    invoke_tool,
    is_tool_allowed,
)
from func.graph.workspace.context_assembler import get_context_assembler
from func.graph.utils.message_history import trim_to_last_turns
from utils.llm.factory import LLMFactory
from utils.logger_operator import LoguruOperator

logger = LoguruOperator.init_app(name="llm_call")

_READ_FILE_RE = re.compile(
    r"(?:read_file|读取|打开|read)\s+[`'\"]?([A-Za-z0-9_./\-]+\.(?:md|txt|yaml|yml|json))[`'\"]?",
    re.IGNORECASE,
)

_TOOL_JSON_RE = re.compile(
    r'\{\s*"tool"\s*:\s*"([a-zA-Z0-9_]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL,
)


def _get_streaming_llm():
    config = LLMConfig()
    llm = LLMFactory.create(config).get_llm()
    if hasattr(llm, "streaming"):
        llm.streaming = True
    return llm


def _stream_text(writer, text: str, chunk_size: int = 8) -> None:
    if not text or writer is None:
        return
    for i in range(0, len(text), chunk_size):
        writer(text[i : i + chunk_size])


def _extract_read_paths(text: str) -> list[str]:
    paths = _READ_FILE_RE.findall(text or "")
    if "SOUL.md" in (text or "") and "SOUL.md" not in paths:
        paths.append("SOUL.md")
    return list(dict.fromkeys(paths))


def _maybe_prefetch_files(messages: list) -> list:
    if not is_tool_allowed("read_file"):
        return messages
    texts = [m.content for m in messages if isinstance(m, HumanMessage) and m.content]
    if not texts:
        return messages
    combined = " ".join(texts)
    paths = _extract_read_paths(combined)
    if not paths:
        return messages

    blocks = []
    for path in paths:
        content = invoke_tool("read_file", {"path": path})
        if not content.startswith("Error"):
            blocks.append(f"[read_file: {path}]\n{content}")

    if not blocks:
        return messages

    injection = HumanMessage(
        content=(
            "以下工作区文件内容已为你加载：\n\n"
            + "\n\n".join(blocks)
            + "\n\n请根据以上内容回答用户问题。"
        )
    )
    return messages + [injection]


def _prepare_messages(state: WorkflowState) -> list:
    assembler = get_context_assembler()
    messages = list(state.get("messages") or [])

    if assembler.should_inject_bootstrap(messages):
        system = assembler.assemble(include_bootstrap=True)
    elif not any(isinstance(m, SystemMessage) for m in messages):
        system = assembler.assemble(include_bootstrap=False)
    else:
        system = None

    max_turns = get_agent_config().max_history_turns
    conv = trim_to_last_turns(messages, max_turns)

    if system is not None:
        return [system] + conv
    return conv


def _extract_text(content) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


def _parse_tool_calls_from_text(text: str) -> list[dict]:
    """模型不支持 native tool calling 时，从 JSON 文本解析工具调用。"""
    calls: list[dict] = []
    for match in _TOOL_JSON_RE.finditer(text or ""):
        name, args_raw = match.group(1), match.group(2)
        try:
            args = json.loads(args_raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(args, dict):
            continue
        calls.append({
            "name": name,
            "args": args,
            "id": str(uuid.uuid4()),
            "type": "tool_call",
        })
    return calls


async def _invoke_with_tools(llm, messages, writer) -> AIMessage:
    """
    带工具的 LLM 调用。
    - 若返回 tool_calls：不输出 content（避免幻觉文字先展示）
    - 若无 tool_calls：流式输出最终回答
    """
    ai_message = await llm.ainvoke(messages)
    if not isinstance(ai_message, AIMessage):
        ai_message = AIMessage(content=str(ai_message))

    if ai_message.tool_calls:
        logger.info(f"tool_calls: {[tc.get('name') for tc in ai_message.tool_calls]}")
        return AIMessage(
            content="",
            tool_calls=ai_message.tool_calls,
            additional_kwargs=getattr(ai_message, "additional_kwargs", {}) or {},
            response_metadata=getattr(ai_message, "response_metadata", {}) or {},
            id=getattr(ai_message, "id", None),
        )

    content = _extract_text(ai_message.content)
    if content and writer is not None:
        _stream_text(writer, content)
    return AIMessage(
        content=content,
        tool_calls=[],
        additional_kwargs=getattr(ai_message, "additional_kwargs", {}) or {},
        response_metadata=getattr(ai_message, "response_metadata", {}) or {},
        id=getattr(ai_message, "id", None),
    )


async def _fallback_without_native_tools(messages, writer) -> AIMessage:
    """bind_tools 失败时的 JSON 工具调用兜底。"""
    json_example = format_json_tool_call_example()
    tool_names = format_tools_prompt_names()
    hint = SystemMessage(
        content=(
            "当前环境不支持原生 tool calling。"
            "需要调用工具时，请仅回复一个 JSON 对象，不要用 Markdown：\n"
            f"{json_example}\n"
            f"可用工具（仅以下）：{tool_names}。\n"
            "工作区根目录固定；除非用户明确要求，不要调用 Get-Location。\n"
            "禁止编造命令输出。回复使用中文。"
        )
    )
    llm = _get_streaming_llm()
    ai_message = await llm.ainvoke(messages + [hint])
    if not isinstance(ai_message, AIMessage):
        ai_message = AIMessage(content=str(ai_message))

    text = _extract_text(ai_message.content)
    tool_calls = _parse_tool_calls_from_text(text)
    if tool_calls:
        logger.info(f"parsed tool_calls from text: {[tc['name'] for tc in tool_calls]}")
        return AIMessage(content="", tool_calls=tool_calls)

    if text and writer is not None:
        _stream_text(writer, text)
    return AIMessage(content=text, tool_calls=[])


async def llm_call(state: WorkflowState) -> dict:
    from langgraph.config import get_stream_writer

    writer = get_stream_writer()
    tools = get_allowed_tools()
    messages = _prepare_messages(state)
    llm_with_tools = _get_streaming_llm().bind_tools(tools)

    try:
        ai_message = await _invoke_with_tools(llm_with_tools, messages, writer)
    except Exception as exc:
        logger.warning(f"bind_tools/ainvoke failed, using fallback: {exc}")
        messages = _maybe_prefetch_files(messages)
        ai_message = await _fallback_without_native_tools(messages, writer)

    response_text = ai_message.content or ""
    return {
        "messages": [ai_message],
        "response": response_text,
    }
