"""PowerShell 命令执行 — 在 workspace 目录运行。"""

from __future__ import annotations

import subprocess

from langchain_core.tools import tool

from config.workspace_config import get_workspace_root

DEFAULT_TIMEOUT_SEC = 30
MAX_OUTPUT_BYTES = 65_536


def _truncate_output(text: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
    return truncated + f"\n... (output truncated, max {max_bytes} bytes)"


def run_powershell(command: str, *, timeout_sec: int = DEFAULT_TIMEOUT_SEC) -> str:
    """在 workspace 目录执行 PowerShell 命令并返回 stdout/stderr。"""
    cmd = (command or "").strip()
    if not cmd:
        return "Error: empty command"

    cwd = get_workspace_root()
    cwd.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout_sec}s"
    except FileNotFoundError:
        return "Error: powershell.exe not found on this system"
    except OSError as e:
        return f"Error: failed to run command: {e}"

    parts = [f"exit_code: {proc.returncode}", f"cwd: {cwd}"]
    if proc.stdout:
        parts.append("stdout:\n" + _truncate_output(proc.stdout))
    if proc.stderr:
        parts.append("stderr:\n" + _truncate_output(proc.stderr))
    if proc.returncode != 0 and not proc.stdout and not proc.stderr:
        parts.append("stderr:\n(non-zero exit, no output captured)")
    return "\n".join(parts)


@tool
def exec_powershell(command: str) -> str:
    """在固定的工作区目录下执行 PowerShell 命令。

    用于脚本、python/pip、git 等。不要用 Get-Location 查路径——工作区根目录已知。
    能用 list_dir / read_file / mkdir / write_file 时优先用专用工具。

    Args:
        command: 纯 PowerShell 命令，例如 'python --version'、'Get-ChildItem demo'。
    """
    return run_powershell(command)
