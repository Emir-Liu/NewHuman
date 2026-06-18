"""文件类 Agent 工具 — read_file, list_dir, write_file, mkdir, edit_file, read_lines, edit_lines。"""

from pathlib import Path

from langchain_core.tools import tool

from config.workspace_config import get_workspace_root, resolve_workspace_path

MAX_READ_BYTES = 32_768


def _format_size(path: Path) -> str:
    if path.is_file():
        return str(path.stat().st_size)
    return "-"


def format_numbered_lines(lines: list[str], start_line: int, width: int = 0) -> str:
    """将文本行格式化为带行号的输出（如 `  12 | content`）。"""
    if not lines:
        return ""
    if width <= 0:
        width = max(len(str(start_line + len(lines) - 1)), 4)
    return "\n".join(f"{start_line + i:>{width}} | {line}" for i, line in enumerate(lines))


def _read_utf8_lines(target: Path) -> list[str]:
    text = target.read_text(encoding="utf-8-sig")
    return text.splitlines()


def _write_utf8_lines(target: Path, lines: list[str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines)
    if lines:
        body += "\n"
    target.write_text(body, encoding="utf-8")


def _resolve_text_file(path: str) -> tuple[Path | None, str | None]:
    """解析工作区文本文件；失败时返回 (None, error_message)。"""
    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return None, f"Error: {e}"
    if not target.is_file():
        return None, f"Error: file not found: {path}"
    size = target.stat().st_size
    if size > MAX_READ_BYTES:
        return None, f"Error: file too large ({size} bytes, max {MAX_READ_BYTES})"
    try:
        _read_utf8_lines(target)
    except UnicodeDecodeError:
        return None, "Error: file is not valid UTF-8 text"
    except OSError as e:
        return None, f"Error: failed to read {path}: {e}"
    return target, None


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


@tool
def edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """在工作区文本文件中查找并替换内容（UTF-8）。

    Args:
        path: 工作区相对路径，例如 demo/notes.txt
        old_string: 要被替换的原文（须与文件中完全一致，含换行与空格）
        new_string: 替换后的新文本
        replace_all: 为 True 时替换所有匹配；默认 False 且仅允许唯一匹配
    """
    if not old_string:
        return "Error: old_string 不能为空"
    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return f"Error: {e}"
    if not target.is_file():
        return f"Error: file not found: {path}"
    try:
        text = target.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return "Error: file is not valid UTF-8 text"

    count = text.count(old_string)
    if count == 0:
        return f"Error: old_string 未在 {path} 中找到"
    if count > 1 and not replace_all:
        return f"Error: 找到 {count} 处匹配，请提供更精确的 old_string 或设置 replace_all=True"

    if replace_all:
        updated = text.replace(old_string, new_string)
        replaced = count
    else:
        updated = text.replace(old_string, new_string, 1)
        replaced = 1

    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as e:
        return f"Error: failed to write {path}: {e}"
    return f"OK: edited {path} ({replaced} replacement(s), {len(updated)} chars)"


@tool
def read_lines(
    path: str,
    start_line: int = 1,
    end_line: int = 0,
    num_lines: int = 0,
) -> str:
    """按行号读取工作区 UTF-8 文本文件，输出行号前缀。

    Args:
        path: 工作区相对路径，如 demo/notes.txt 或 memory/conversations/2026-06-18.md
        start_line: 起始行号（从 1 开始）
        end_line: 结束行号（含）；0 表示未指定
        num_lines: 读取行数；与 end_line 均为 0 时读到文件末尾
    """
    target, err = _resolve_text_file(path)
    if err:
        return err
    assert target is not None

    all_lines = _read_utf8_lines(target)
    total = len(all_lines)
    if start_line < 1:
        start_line = 1
    if start_line > total and total > 0:
        return f"Error: start_line={start_line} 超出文件行数（共 {total} 行）"

    if end_line > 0:
        end = min(end_line, total)
    elif num_lines > 0:
        end = min(start_line - 1 + num_lines, total)
    else:
        end = total

    if end < start_line:
        return f"Error: 无效行范围 start={start_line} end={end}（文件共 {total} 行）"

    chunk = all_lines[start_line - 1 : end]
    if not chunk:
        return f"Error: 无内容（文件共 {total} 行，start_line={start_line}）"

    numbered = format_numbered_lines(chunk, start_line)
    return f"File: {path} (lines {start_line}-{end} of {total})\n{numbered}"


@tool
def edit_lines(
    path: str,
    start_line: int,
    end_line: int,
    new_content: str,
    insert: bool = False,
) -> str:
    """按行号替换或插入工作区 UTF-8 文本文件内容。

    Args:
        path: 工作区相对路径
        start_line: 起始行号（从 1 开始）；insert=True 时在此行前插入
        end_line: 结束行号（含）；insert=True 时忽略
        new_content: 新文本（可含多行）
        insert: True 时在 start_line 前插入，不删除原有行
    """
    if start_line < 1:
        return "Error: start_line 须 >= 1"

    if not insert and end_line < start_line:
        return "Error: end_line 须 >= start_line"

    try:
        target = resolve_workspace_path(path)
    except ValueError as e:
        return f"Error: {e}"

    if target.is_file():
        try:
            all_lines = _read_utf8_lines(target)
        except UnicodeDecodeError:
            return "Error: file is not valid UTF-8 text"
        except OSError as e:
            return f"Error: failed to read {path}: {e}"
    elif insert:
        all_lines = []
    else:
        return f"Error: file not found: {path}"

    total = len(all_lines)
    new_lines = (new_content or "").splitlines()
    start_idx = start_line - 1

    if insert:
        if start_idx > total:
            return f"Error: start_line={start_line} 超出文件行数（共 {total} 行）"
        updated = all_lines[:start_idx] + new_lines + all_lines[start_idx:]
        action = f"inserted {len(new_lines)} line(s) before line {start_line}"
    else:
        if start_idx >= total and total > 0:
            return f"Error: start_line={start_line} 超出文件行数（共 {total} 行）"
        end_idx = min(end_line, total)
        if end_idx < start_line:
            return f"Error: 无效行范围 start={start_line} end={end_line}（文件共 {total} 行）"
        updated = all_lines[:start_idx] + new_lines + all_lines[end_idx:]
        replaced = end_idx - start_idx
        action = f"replaced lines {start_line}-{end_idx} ({replaced} line(s)) with {len(new_lines)} line(s)"

    try:
        _write_utf8_lines(target, updated)
    except OSError as e:
        return f"Error: failed to write {path}: {e}"
    return f"OK: {action} in {path} (now {len(updated)} lines)"
