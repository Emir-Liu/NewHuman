"""组装 Agent System Prompt — Bootstrap + Skills 索引。"""

from __future__ import annotations

from langchain_core.messages import AnyMessage, SystemMessage

from func.graph.tools.tool_registry import (
    format_tools_prompt_names,
    format_tools_prompt_table,
    format_tools_usage_notes,
    is_tool_allowed,
)
from func.graph.workspace.manager import BOOTSTRAP_FILES, get_workspace_manager


class ContextAssembler:
    """新 session 首轮注入 Bootstrap；每轮附带 Skills 索引。"""

    def __init__(self, manager=None) -> None:
        self.manager = manager or get_workspace_manager()

    def _skills_block(self) -> str:
        skills = self.manager.list_skills()
        if not skills:
            return ""
        lines = ["## 可用技能"]
        if is_tool_allowed("read_file"):
            lines[0] += "（需要时用 read_file 读取完整 SKILL.md）"
        else:
            lines[0] += "（路径如下，可用 exec_powershell 读取文件内容）"
        for s in skills:
            desc = s["description"] or "无描述"
            lines.append(f"- **{s['name']}**：{desc} — `{s['path']}`")
        return "\n".join(lines)

    def _tool_rules(self) -> str:
        root = self.manager.root
        tool_table = format_tools_prompt_table()
        usage_notes = format_tools_usage_notes()
        notes_block = f"\n{usage_notes}\n" if usage_notes else "\n"

        return f"""## 工具使用规则

你拥有真实可用的工具（**仅以下 {format_tools_prompt_names()}**）。
**工作区根目录（所有工具的当前工作目录）固定为：** `{root}`

**以下情况不要调用工具：** 打招呼、闲聊、普通问答，或不需要新的文件/命令结果的追问。
**不要调用 Get-Location** 来确认路径——除非用户明确要求当前路径，否则你已知路径是 `{root}`。
**不要重复** 用户在本对话中已经看到过的目录/路径信息。

**禁止编造工具结果。** 不要在 Markdown 代码块里写假的 PowerShell 输出。
仅在用户请求需要获取新数据，或需要操作文件/执行命令时，才调用工具。
**不要调用未在上表中列出的工具。**

| 说明 | 工具名 | 参数示例 |
|------|--------|----------|
{tool_table}
{notes_block}
## 错误自愈

- 工具返回 `exit_code` 非 0、stderr 报错、或以 `Error:` 开头时，视为**执行失败**。
- 失败后：根据 ToolMessage 中的输出**自行分析原因**，修正命令或参数，**再次调用工具**重试。
- 同一用户请求内，最多自主重试 **3 次**；仍失败再向用户说明原因和已尝试的步骤。
- 用户已说「帮我执行 / 你来做 / 直接跑」时：**立即执行**，禁止问「是否继续」「请确认」。
- 禁止用 Markdown 代码块假装已执行；**只有工具返回的结果**才算真实输出。

**回复语言：** 默认使用中文（见 USER.md）。"""

    def assemble(self, *, include_bootstrap: bool = True) -> SystemMessage:
        self.manager.ensure_initialized()
        parts = [
            "你是 NewHuman，一个带工具的个人 AI 助手。",
            self._tool_rules(),
        ]

        if include_bootstrap:
            for name in BOOTSTRAP_FILES:
                content = self.manager.read_bootstrap(name)
                if content.strip():
                    parts.append(f"\n## {name}\n{content.strip()}")

        skills = self._skills_block()
        if skills:
            parts.append(f"\n{skills}")

        return SystemMessage(content="\n".join(parts))

    def should_inject_bootstrap(self, messages: list[AnyMessage]) -> bool:
        """无历史 SystemMessage 时视为新 session 首轮。"""
        return not any(isinstance(m, SystemMessage) for m in messages)


_default_assembler: ContextAssembler | None = None


def get_context_assembler() -> ContextAssembler:
    global _default_assembler
    if _default_assembler is None:
        _default_assembler = ContextAssembler()
    return _default_assembler
