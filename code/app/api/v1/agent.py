"""Agent 能力与 Workspace 元信息 API。"""

from __future__ import annotations

from fastapi import APIRouter

from config.workspace_config import get_workspace_root
from func.graph.tools.tool_registry import get_allowed_tools
from func.graph.workspace.manager import get_workspace_manager

router = APIRouter(prefix="/agent", tags=["Agent"])

_TOOL_GROUPS: dict[str, str] = {
    "exec_powershell": "terminal",
    "read_lines": "terminal",
    "edit_lines": "terminal",
    "memory_append": "memory",
    "memory_read": "memory",
    "memory_get": "memory",
    "memory_search": "memory",
    "memory_update_summary": "memory",
    "fetch_url": "web",
    "list_agent_roles": "multi_agent",
    "delegate_subagent": "multi_agent",
}

_GROUP_LABELS: dict[str, str] = {
    "terminal": "终端与工作区",
    "memory": "文件记忆",
    "web": "网络",
    "multi_agent": "多智能体",
}

_QUICK_PROMPTS = [
    {"label": "记住偏好", "text": "请记住：我喜欢简洁的中文回复"},
    {"label": "列出 Skills", "text": "列出 skills 目录下有哪些技能，并简要说明"},
    {"label": "抓取网页", "text": "用 fetch_url 抓取 https://example.com 并总结"},
    {"label": "方案对比", "text": "帮我对比 Python asyncio 与 threading 的适用场景，可分步委派子 Agent"},
]


@router.get("/capabilities")
async def get_capabilities():
    """返回当前注册工具、Skills 与示例提示（供 Chat UI 展示）。"""
    mgr = get_workspace_manager()
    mgr.ensure_initialized()

    groups: dict[str, list[dict[str, str]]] = {
        "terminal": [],
        "memory": [],
        "web": [],
        "multi_agent": [],
    }

    for tool in get_allowed_tools():
        gid = _TOOL_GROUPS.get(tool.name, "terminal")
        desc = (tool.description or tool.name).strip().split("\n")[0]
        groups[gid].append({"name": tool.name, "description": desc})

    tool_groups = [
        {"id": gid, "label": _GROUP_LABELS[gid], "tools": groups[gid]}
        for gid in ("terminal", "memory", "web", "multi_agent")
        if groups[gid]
    ]

    return {
        "workspace_root": str(get_workspace_root()),
        "memory": {
            "summary": "MEMORY.md",
            "daily_dir": "memory/",
        },
        "tool_groups": tool_groups,
        "skills": mgr.list_skills(),
        "quick_prompts": _QUICK_PROMPTS,
    }
