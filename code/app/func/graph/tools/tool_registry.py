"""MVP 工具注册与 allow 策略（M1 起逐步扩展）。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool

from func.graph.tools.file_tool import list_dir, mkdir, read_file, write_file
from func.graph.tools.powershell_tool import exec_powershell

# _MVP_TOOLS: list[BaseTool] = [read_file, list_dir, write_file, mkdir, exec_powershell]
_MVP_TOOLS: list[BaseTool] = [exec_powershell]

tools_by_name: dict[str, BaseTool] = {t.name: t for t in _MVP_TOOLS}

# 参数占位示例（schema 无 default 时使用）
_ARG_PLACEHOLDERS: dict[str, dict[str, Any]] = {
    "read_file": {"path": "SOUL.md"},
    "list_dir": {"path": "."},
    "write_file": {"path": "demo/hello.txt", "content": "你好"},
    "mkdir": {"path": "demo/subdir"},
    "exec_powershell": {"command": "python --version"},
}


def get_allowed_tools() -> list[BaseTool]:
    return list(_MVP_TOOLS)


def get_allowed_tool_names() -> list[str]:
    return [t.name for t in _MVP_TOOLS]


def is_tool_allowed(name: str) -> bool:
    return name in tools_by_name


def example_args_for_tool(tool: BaseTool) -> dict[str, Any]:
    """根据工具 schema 生成 JSON 参数示例。"""
    if tool.name in _ARG_PLACEHOLDERS:
        return dict(_ARG_PLACEHOLDERS[tool.name])
    try:
        schema = tool.get_input_schema()
        props = schema.model_json_schema().get("properties", {})
        example: dict[str, Any] = {}
        for field, spec in props.items():
            if "default" in spec:
                example[field] = spec["default"]
            elif spec.get("type") == "string":
                example[field] = ""
            elif spec.get("type") in ("integer", "number"):
                example[field] = 0
            elif spec.get("type") == "boolean":
                example[field] = False
            else:
                example[field] = ""
        return example
    except Exception:
        return {}


def format_tool_args_example(tool: BaseTool) -> str:
    return json.dumps(example_args_for_tool(tool), ensure_ascii=False)


def format_json_tool_call_example(tool: BaseTool | None = None) -> str:
    """JSON 兜底模式下的单条调用示例。"""
    target = tool or (_MVP_TOOLS[0] if _MVP_TOOLS else None)
    if target is None:
        return '{"tool": "unknown", "args": {}}'
    payload = {"tool": target.name, "args": example_args_for_tool(target)}
    return json.dumps(payload, ensure_ascii=False)


def format_tools_prompt_table() -> str:
    """生成 system prompt 中的工具 Markdown 表格（仅当前注册工具）。"""
    tools = get_allowed_tools()
    if not tools:
        return "（当前未注册任何工具）"

    rows: list[str] = []
    for tool in tools:
        desc = (tool.description or tool.name).strip().split("\n")[0]
        rows.append(f"| {desc} | `{tool.name}` | `{format_tool_args_example(tool)}` |")
    return "\n".join(rows)


def format_tools_prompt_names() -> str:
    """可用工具名称列表，用于兜底提示。"""
    names = get_allowed_tool_names()
    return "、".join(names) if names else "（无）"


def format_tools_usage_notes() -> str:
    """根据已注册工具生成补充说明。"""
    names = set(get_allowed_tool_names())
    notes: list[str] = []
    if "list_dir" in names and "exec_powershell" in names:
        notes.append("列目录优先用 `list_dir`，不要用 `Get-ChildItem`。")
    if "exec_powershell" in names:
        notes.append(
            "调用 exec_powershell 时，`command` 里只写 PowerShell 命令本身，"
            "不要写 `exec_powershell \"...\"`。"
        )
    if "read_file" not in names and "exec_powershell" in names:
        notes.append("当前未注册 read_file；读文件可用 exec_powershell 执行 Get-Content。")
    return "\n".join(notes)


def invoke_tool(name: str, args: dict[str, Any]) -> str:
    tool = tools_by_name.get(name)
    if tool is None:
        return f"Error: tool '{name}' is not allowed or not registered."
    try:
        result = tool.invoke(args)
        return str(result)
    except Exception as e:
        return f"Error executing {name}: {e}"
