"""文件型记忆工具 — 对标 OpenClaw，Markdown 存于 workspace。"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from langchain_core.tools import tool

from config.workspace_config import get_workspace_root, resolve_workspace_path
from func.graph.tools.file_tool import format_numbered_lines

MEMORY_SUMMARY = "MEMORY.md"
MEMORY_DIR = "memory"
MAX_READ_BYTES = 32_768
MAX_SEARCH_RESULTS = 20


def _today_daily_path() -> str:
    return f"{MEMORY_DIR}/{date.today().isoformat()}.md"


def _is_allowed_memory_path(rel: str) -> bool:
    norm = rel.replace("\\", "/").lstrip("/")
    if norm == MEMORY_SUMMARY:
        return True
    if norm.startswith(f"{MEMORY_DIR}/") and norm.endswith(".md"):
        return True
    return False


def _resolve_memory_path(rel: str) -> Path:
    if not _is_allowed_memory_path(rel):
        raise ValueError(f"仅允许读取 MEMORY.md 或 {MEMORY_DIR}/*.md: {rel}")
    return resolve_workspace_path(rel)


def _ensure_memory_dirs() -> None:
    root = get_workspace_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / MEMORY_DIR).mkdir(exist_ok=True)


def _append_to_file(rel: str, note: str) -> str:
    _ensure_memory_dirs()
    target = _resolve_memory_path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = f"\n\n## {stamp}\n\n{note.strip()}\n"
    if target.is_file():
        existing = target.read_text(encoding="utf-8-sig")
        target.write_text(existing.rstrip() + block, encoding="utf-8")
    else:
        header = f"# {target.name}\n"
        target.write_text(header + block.lstrip("\n"), encoding="utf-8")
    return f"OK: appended to {rel} ({len(note)} chars)"


def _list_memory_files() -> list[Path]:
    root = get_workspace_root()
    files: list[Path] = []
    summary = root / MEMORY_SUMMARY
    if summary.is_file():
        files.append(summary)
    mem_dir = root / MEMORY_DIR
    if mem_dir.is_dir():
        files.extend(sorted(mem_dir.glob("**/*.md"), reverse=True))
    return files


@tool
def memory_append(note: str, target: str = "daily") -> str:
    """追加一条记忆到 Markdown 文件。

    Args:
        note: 要记住的内容（事实、偏好、决定等）
        target: `daily` 写入今日日志 memory/YYYY-MM-DD.md；`summary` 写入 MEMORY.md
    """
    if not (note or "").strip():
        return "Error: note 不能为空"
    rel = MEMORY_SUMMARY if target.strip().lower() == "summary" else _today_daily_path()
    try:
        return _append_to_file(rel, note)
    except ValueError as e:
        return f"Error: {e}"
    except OSError as e:
        return f"Error: failed to append: {e}"


@tool
def memory_read(path: str = "", start_line: int = 1, num_lines: int = 0) -> str:
    """读取记忆文件；path 为空时列出最近记忆文件及摘要。

    Args:
        path: 相对路径，如 MEMORY.md 或 memory/2026-06-18.md；留空则列出可用文件
        start_line: 起始行号（从 1 开始）
        num_lines: 读取行数，0 表示读到文件末尾
    """
    _ensure_memory_dirs()
    if not (path or "").strip():
        files = _list_memory_files()
        if not files:
            return f"（尚无记忆文件；可用 memory_append 写入 {MEMORY_SUMMARY} 或 {_today_daily_path()}）"
        lines = ["可用记忆文件："]
        root = get_workspace_root()
        for f in files[:15]:
            rel = f.relative_to(root).as_posix()
            size = f.stat().st_size
            preview = ""
            try:
                text = f.read_text(encoding="utf-8-sig", errors="replace")
                for raw in text.splitlines():
                    s = raw.strip()
                    if s and not s.startswith("#"):
                        preview = s[:120]
                        break
            except OSError:
                preview = "(无法读取)"
            suffix = f" — {preview}" if preview else ""
            lines.append(f"- `{rel}` ({size} bytes){suffix}")
        return "\n".join(lines)

    try:
        target = _resolve_memory_path(path.strip())
    except ValueError as e:
        return f"Error: {e}"
    if not target.is_file():
        return f"Error: memory file not found: {path}"
    size = target.stat().st_size
    if size > MAX_READ_BYTES:
        return f"Error: file too large ({size} bytes, max {MAX_READ_BYTES})"
    try:
        text = target.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return "Error: file is not valid UTF-8 text"

    all_lines = text.splitlines()
    if start_line < 1:
        start_line = 1
    if num_lines <= 0:
        chunk = all_lines[start_line - 1 :]
    else:
        chunk = all_lines[start_line - 1 : start_line - 1 + num_lines]
    if not chunk:
        return f"Error: 无内容（文件共 {len(all_lines)} 行，start_line={start_line}）"
    numbered = format_numbered_lines(chunk, start_line)
    return f"File: {path}\n{numbered}"


@tool
def memory_get(path: str, start_line: int = 1, num_lines: int = 0) -> str:
    """按路径读取记忆片段（与 memory_read 相同，兼容 OpenClaw 命名）。"""
    return memory_read.invoke(
        {"path": path, "start_line": start_line, "num_lines": num_lines}
    )


@tool
def memory_search(query: str, max_results: int = 10) -> str:
    """在 MEMORY.md 与 memory/*.md 中按关键词搜索（不依赖向量库）。

    Args:
        query: 搜索关键词或短语（空格分隔多个词时须全部匹配）
        max_results: 最多返回条数
    """
    q = (query or "").strip()
    if not q:
        return "Error: query 不能为空"
    max_results = max(1, min(int(max_results), MAX_SEARCH_RESULTS))
    terms = [t for t in re.split(r"\s+", q.lower()) if t]
    if not terms:
        return "Error: query 不能为空"

    _ensure_memory_dirs()
    hits: list[tuple[int, str, int, str]] = []

    for fpath in _list_memory_files():
        try:
            text = fpath.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        rel = fpath.relative_to(get_workspace_root()).as_posix()
        for i, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if all(term in lower for term in terms):
                hits.append((0 if rel == MEMORY_SUMMARY else 1, rel, i, line.strip()))
                if len(hits) >= max_results * 3:
                    break

    if not hits:
        return f"未找到包含「{query}」的记忆（可先用 memory_read 浏览文件）"

    hits.sort(key=lambda x: (x[0], x[1], x[2]))
    hits = hits[:max_results]
    lines = [f"搜索「{query}」共 {len(hits)} 条："]
    for _, rel, line_no, content in hits:
        snippet = content[:200] + ("…" if len(content) > 200 else "")
        lines.append(f"- `{rel}:{line_no}` {snippet}")
    return "\n".join(lines)


@tool
def memory_update_summary(content: str, mode: str = "append") -> str:
    """更新长期记忆摘要 MEMORY.md。

    Args:
        content: 要写入的 Markdown 文本
        mode: `append` 追加段落；`replace` 覆盖整个文件
    """
    if not (content or "").strip():
        return "Error: content 不能为空"
    _ensure_memory_dirs()
    target = resolve_workspace_path(MEMORY_SUMMARY)
    try:
        if mode.strip().lower() == "replace":
            header = "# MEMORY\n\n"
            body = content.strip()
            if not body.startswith("#"):
                body = header + body + "\n"
            target.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
            return f"OK: replaced {MEMORY_SUMMARY} ({len(content)} chars)"
        return _append_to_file(MEMORY_SUMMARY, content)
    except OSError as e:
        return f"Error: failed to update summary: {e}"
