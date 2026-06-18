"""对话历史裁剪 — 仅影响发给 LLM 的上下文，不修改 checkpoint。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage


def trim_to_last_turns(messages: list, max_turns: int) -> list:
    """
    保留最近 max_turns 轮用户消息及其后的 AI/Tool 回复。

    max_turns <= 0 表示不裁剪。
    """
    if max_turns <= 0 or not messages:
        return list(messages)

    conv = [m for m in messages if not isinstance(m, SystemMessage)]
    human_indices = [i for i, m in enumerate(conv) if isinstance(m, HumanMessage)]
    if len(human_indices) <= max_turns:
        return conv

    start = human_indices[-max_turns]
    return conv[start:]
