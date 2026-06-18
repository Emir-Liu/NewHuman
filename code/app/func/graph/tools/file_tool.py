"""文件类 Agent 工具 — read_file, list_dir。"""

from pathlib import Path

from langchain_core.tools import tool

from config.workspace_config import get_workspace_root, resolve_workspace_path

MAX_READ_BYTES = 32_768


def _format_size(path: Path) -> str:
    if path.is_file():
        return str(path.stat().st_size)
    return "-"


@tool
def read_file(path: str) -> str:
    """从工作区读取文本文件。路径示例：SOUL.md 或 skills/kb-qa/SKILL.md。"""
    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return f"Error: {e}"
    if not target.is_file():
        return f"Error: file not found: {path}"
    size = target.stat().st_size
    if size > MAX_READ_BYTES:
        return f"Error: file too large ({size} bytes, max {MAX_READ_BYTES})"
    try:
        text = target.read_text(encoding="utf-8-sig")
        return text
    except UnicodeDecodeError:
        return "Error: file is not valid UTF-8 text"


@tool
def list_dir(path: str = ".") -> str:
    """列出工作区指定路径下的文件和文件夹（默认：工作区根目录）。"""
    try:
        target = resolve_workspace_path(path or ".")
    except ValueError as e:
        return f"Error: {e}"
    if not target.is_dir():
        return f"Error: not a directory: {path}"
    lines = [f"Listing: {target.relative_to(get_workspace_root()) or '.'}"]
    for entry in sorted(target.iterdir()):
        kind = "dir" if entry.is_dir() else "file"
        lines.append(f"  [{kind}] {entry.name} ({_format_size(entry)} bytes)" if kind == "file" else f"  [dir] {entry.name}/")
    return "\n".join(lines)


@tool
def write_file(path: str, content: str) -> str:
    """在工作区创建或覆盖 UTF-8 文本文件。"""
    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return f"Error: {e}"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content or "", encoding="utf-8")
        return f"OK: wrote {path} ({len(content or '')} chars)"
    except OSError as e:
        return f"Error: failed to write {path}: {e}"


@tool
def mkdir(path: str) -> str:
    """在工作区创建文件夹（会自动创建上级目录）。"""
    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return f"Error: {e}"
    try:
        target.mkdir(parents=True, exist_ok=True)
        rel = target.relative_to(get_workspace_root())
        return f"OK: created directory {rel}"
    except OSError as e:
        return f"Error: failed to create directory {path}: {e}"
