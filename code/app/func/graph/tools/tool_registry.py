"""MVP 工具注册与 allow 策略（M1 起逐步扩展）。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool

from func.graph.tools.file_tool import edit_lines, read_lines
from func.graph.tools.memory_tool import (
    memory_append,
    memory_get,
    memory_read,
    memory_search,
    memory_update_summary,
)
from func.graph.tools.powershell_tool import exec_powershell
from func.graph.tools.subagent_context import get_subagent_depth
from func.graph.tools.subagent_tool import delegate_subagent, list_agent_roles
from func.graph.tools.web_tool import fetch_url

_MVP_TOOLS: list[BaseTool] = [
    exec_powershell,
    read_lines,
    edit_lines,
    memory_append,
    memory_read,
    memory_get,
    memory_search,
    memory_update_summary,
    fetch_url,
    list_agent_roles,
    delegate_subagent,
]

tools_by_name: dict[str, BaseTool] = {t.name: t for t in _MVP_TOOLS}

# 参数占位示例（schema 无 default 时使用）
_ARG_PLACEHOLDERS: dict[str, dict[str, Any]] = {
    "exec_powershell": {"command": "Get-ChildItem -Name"},
    "read_lines": {"path": "demo/notes.txt", "start_line": 1, "end_line": 20, "num_lines": 0},
    "edit_lines": {
        "path": "demo/notes.txt",
        "start_line": 5,
        "end_line": 7,
        "new_content": "新内容行",
        "insert": False,
    },
    "memory_append": {"note": "用户喜欢简洁回复", "target": "daily"},
    "memory_read": {"path": "MEMORY.md", "start_line": 1, "num_lines": 0},
    "memory_get": {"path": "MEMORY.md", "start_line": 1, "num_lines": 0},
    "memory_search": {"query": "小明", "max_results": 5},
    "memory_update_summary": {"content": "用户叫小明", "mode": "append"},
    "fetch_url": {"url": "https://example.com"},
    "list_agent_roles": {},
    "delegate_subagent": {
        "task": "调研 Python 异步框架并列出优缺点",
        "role": "researcher",
        "context": "用户需要技术选型参考",
    },
}


def get_allowed_tools() -> list[BaseTool]:
    tools = list(_MVP_TOOLS)
    if get_subagent_depth() > 0:
        tools = [t for t in tools if t.name != "delegate_subagent"]
    return tools


def get_allowed_tool_names() -> list[str]:
    return [t.name for t in get_allowed_tools()]


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
    if "exec_powershell" in names:
        notes.append(
            "工作区文件操作用 `exec_powershell`（cwd 已是工作区根，路径用相对路径）："
            "列目录 `Get-ChildItem -Name <path>`；"
            "写文件 `Set-Content -Path <path> -Value '...' -Encoding UTF8`；"
            "建目录 `New-Item -ItemType Directory -Path <path> -Force`。"
            "按行号读/改文本优先用 `read_lines` / `edit_lines`（输出含行号，比 Get-Content 更精确）。"
        )
        notes.append(
            "调用 exec_powershell 时，`command` 里只写 PowerShell 命令本身，"
            "不要写 `exec_powershell \"...\"`。"
        )
    if "fetch_url" in names and "exec_powershell" in names:
        notes.append("抓取网页用 `fetch_url`（含 SSRF 防护），不要用 Invoke-WebRequest / curl。")
    if "memory_search" in names:
        notes.append(
            "记忆存于 `MEMORY.md`（长期摘要）、`memory/YYYY-MM-DD.md`（日志）"
            "与 `memory/conversations/YYYY-MM-DD.md`（自动对话记录）；"
            "回忆时用 `memory_search` + `memory_read` 或 `read_lines`；写入用 `memory_append`。"
        )
    if "exec_powershell" in names:
        notes.append(
            "技能位于 `skills/<名称>/SKILL.md`；系统提示「可用技能」仅为摘要，"
            "执行前用 `Get-Content skills/<名称>/SKILL.md -Encoding UTF8` 读全文；"
            "`Get-ChildItem -Name skills` 可列出全部技能目录。"
        )
        notes.append(
            "创建新技能：先 `Get-Content skills/skill-creator/SKILL.md -Encoding UTF8`，"
            "再用 `New-Item` + `Set-Content` 创建 `skills/<名称>/SKILL.md`。"
        )
    if "delegate_subagent" in names:
        notes.append(
            "复杂任务可分解后调用 `delegate_subagent` 委派子 Agent；"
            "子 Agent 无父对话历史，须在 task/context 写清背景；"
            "可用 `list_agent_roles` 查看 researcher/coder/reviewer/summarizer 等预设角色。"
        )
    return "\n".join(notes)


async def invoke_tool_async(name: str, args: dict[str, Any]) -> str:
    tool = tools_by_name.get(name)
    if tool is None:
        return f"Error: tool '{name}' is not allowed or not registered."
    try:
        if hasattr(tool, "ainvoke"):
            result = await tool.ainvoke(args)
        else:
            result = tool.invoke(args)
        return str(result)
    except Exception as e:
        return f"Error executing {name}: {e}"


def invoke_tool(name: str, args: dict[str, Any]) -> str:
    tool = tools_by_name.get(name)
    if tool is None:
        return f"Error: tool '{name}' is not allowed or not registered."
    try:
        result = tool.invoke(args)
        return str(result)
    except Exception as e:
        return f"Error executing {name}: {e}"
