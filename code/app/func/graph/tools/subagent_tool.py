"""子 Agent 委派 — 隔离上下文嵌套运行 ReAct 图。"""

from __future__ import annotations

import asyncio
import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from config.agent_config import get_agent_config
from func.graph.tools.subagent_context import get_subagent_depth, subagent_depth_scope

AGENT_ROLES: dict[str, str] = {
    "researcher": "调研与分析：检索资料、对比方案、输出结构化结论",
    "coder": "代码实现：读写文件、执行命令、修复错误",
    "reviewer": "审查与质检：检查逻辑、风险与改进建议",
    "summarizer": "汇总整理：合并多源信息为简洁报告",
}

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        from func.graph.build import build_graph

        _graph = build_graph()
    return _graph


def reset_subagent_graph_cache() -> None:
    """测试或热重载时清空缓存图。"""
    global _graph
    _graph = None


def _format_subagent_task(task: str, role: str, context: str) -> str:
    parts: list[str] = []
    if role.strip():
        key = role.strip().lower()
        desc = AGENT_ROLES.get(key, role.strip())
        parts.append(f"【角色】{key} — {desc}")
    parts.append(f"【任务】{task.strip()}")
    if context.strip():
        parts.append(f"【背景】{context.strip()}")
    parts.append(
        "请独立完成上述子任务。只输出与任务相关的结论与要点，"
        "不要提及委派、子 Agent 或主对话。"
    )
    return "\n\n".join(parts)


def _extract_final_answer(result: dict) -> str:
    answer = (result.get("response") or "").strip()
    if answer:
        return answer

    messages = result.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            if getattr(msg, "tool_calls", None):
                continue
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            if text.strip():
                return text.strip()
    return "（子 Agent 未返回文本结果）"


async def _invoke_subagent_graph(task_message: str) -> str:
    graph = _get_graph()
    thread_id = f"subagent-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    with subagent_depth_scope():
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=task_message)],
                "query": task_message,
            },
            config=config,
        )
    return _extract_final_answer(result)


@tool
async def delegate_subagent(task: str, role: str = "", context: str = "") -> str:
    """将子任务委派给独立子 Agent 执行（隔离对话历史，仅接收任务简报）。

    适用于复杂任务分解：主 Agent 拆分后逐个委派，再汇总子 Agent 返回的结论。
    子 Agent 与主 Agent 共享同一工作区沙箱，但看不到父对话全文。

    Args:
        task: 子任务描述（必填，应自洽、可独立执行）
        role: 可选预设角色：researcher / coder / reviewer / summarizer，或自定义角色名
        context: 可选额外背景（勿粘贴整段父对话，只写子任务必需信息）
    """
    if not task or not task.strip():
        return "Error: task 不能为空"

    cfg = get_agent_config()
    if get_subagent_depth() >= cfg.max_subagent_depth:
        return (
            f"Error: 已达子 Agent 最大嵌套深度 ({cfg.max_subagent_depth})，"
            "无法再委派。请由主 Agent 直接完成或合并子任务。"
        )

    brief = _format_subagent_task(task, role, context)
    try:
        result = await asyncio.wait_for(
            _invoke_subagent_graph(brief),
            timeout=cfg.subagent_timeout_sec,
        )
    except asyncio.TimeoutError:
        return f"Error: 子 Agent 执行超时（{cfg.subagent_timeout_sec}s）"
    except Exception as exc:
        return f"Error: 子 Agent 执行失败: {exc}"

    max_len = 12000
    if len(result) > max_len:
        return result[:max_len] + "\n...(truncated)"
    return result


@tool
def list_agent_roles() -> str:
    """列出可用的子 Agent 预设角色及说明，用于任务分解与 delegate_subagent 的 role 参数。"""
    return json.dumps(AGENT_ROLES, ensure_ascii=False, indent=2)
