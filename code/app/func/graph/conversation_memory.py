"""自动将每轮对话追加写入 workspace 记忆文件。"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from config.agent_config import get_agent_config
from config.workspace_config import get_workspace_root, resolve_workspace_path

logger = logging.getLogger(__name__)

DEFAULT_CONVERSATIONS_DIR = "memory/conversations"


def _conversation_daily_path(mem_dir: str) -> str:
    return f"{mem_dir.rstrip('/')}/{date.today().isoformat()}.md"


def save_conversation_turn(
    conversation_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """将一轮 user+assistant 交换追加到按日分文件的对话日志。"""
    cfg = get_agent_config()
    if not cfg.conversation_memory_enabled:
        return

    user_text = (user_message or "").strip()
    assistant_text = (assistant_message or "").strip()
    if not user_text and not assistant_text:
        return

    mem_dir = (cfg.conversation_memory_dir or DEFAULT_CONVERSATIONS_DIR).strip()
    rel = _conversation_daily_path(mem_dir)

    try:
        target = resolve_workspace_path(rel)
    except ValueError as e:
        logger.warning("conversation memory path rejected: %s", e)
        return

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = (
        f"\n\n## {stamp} — conversation {conversation_id}\n\n"
        f"### User\n\n{user_text}\n\n"
        f"### Assistant\n\n{assistant_text}\n"
    )

    try:
        _append_markdown(target, block)
        logger.debug("saved conversation turn to %s", rel)
    except OSError as e:
        logger.warning("failed to save conversation memory: %s", e)


def _append_markdown(target: Path, block: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    root = get_workspace_root()
    root.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        existing = target.read_text(encoding="utf-8-sig")
        target.write_text(existing.rstrip() + block, encoding="utf-8")
    else:
        header = f"# 对话记录 {target.stem}\n"
        target.write_text(header + block.lstrip("\n"), encoding="utf-8")
