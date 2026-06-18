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
        lines = ["## 可用技能（Skills）"]
        if is_tool_allowed("exec_powershell"):
            lines.append(
                "以下为摘要索引。**执行某技能前**，用 `exec_powershell` 执行 "
                "`Get-Content skills/<名称>/SKILL.md -Encoding UTF8` 读全文；"
                "`Get-ChildItem -Name skills` 可发现全部技能目录。"
            )
        else:
            lines.append("以下为摘要索引；需要完整说明时按路径读取 SKILL.md。")
        for s in skills:
            desc = s["description"] or "无描述"
            lines.append(f"- **{s['name']}**：{desc} — `{s['path']}`")
        if any(s["name"] == "skill-creator" for s in skills):
            lines.append(
                "用户要求**创建、编写或学习技能**时，先 "
                "`Get-Content skills/skill-creator/SKILL.md -Encoding UTF8`。"
            )
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

    def _multi_agent_block(self) -> str:
        if not is_tool_allowed("delegate_subagent"):
            return ""
        return """## 多 Agent 协作（任务编排）

当用户请求**明显复杂**（多步骤、需并行调研、多领域专长、对比多个方案）时：

1. **评估**：判断是否值得拆分；寒暄、单步读文件/命令、简单问答**不要**委派。
2. **分解**：将工作拆成 2–4 个可独立完成的子任务。
3. **委派**：对每个子任务调用 `delegate_subagent`（可选 `role`：researcher / coder / reviewer / summarizer）。
4. **汇总**：收到全部子 Agent 结果后，由你综合对比并给出最终建议。

**规则：**
- 子 Agent **看不到**本对话历史；须在 `task` / `context` 中写清子任务必需背景。
- 同一用户请求内可**顺序**多次调用 `delegate_subagent`；子 Agent **不能**再委派（嵌套深度受限）。
- 委派前可用 `list_agent_roles` 查看预设角色；完整示例见 `skills/multi-agent/SKILL.md`。
- 示例：用户要对比两个方案 → 分别委派「调研方案 A」「调研方案 B」，再合成对比表。

**单 Agent 即可：** 打招呼、一次工具调用能完成的操作、对已有结果的追问。"""

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

        if is_tool_allowed("memory_search"):
            parts.append(
                "\n## 记忆（文件存储）\n"
                "长期摘要：`MEMORY.md`；日誌：`memory/YYYY-MM-DD.md`；"
                "对话记录（每轮自动保存）：`memory/conversations/YYYY-MM-DD.md`。"
                "MEMORY 不会每轮全量注入，需要回忆时主动调用 `memory_search`、"
                "`memory_read` 或 `read_lines`；"
                "用户要求记住信息时用 `memory_append`（日常）或 `memory_update_summary`（长期摘要）。"
            )

        multi_agent = self._multi_agent_block()
        if multi_agent:
            parts.append(f"\n{multi_agent}")

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
