"""Workspace 路径配置。"""

import os
from pathlib import Path

# code/app/config/workspace_config.py -> repo root = parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_WS = _REPO_ROOT / "workspace" / "default"


def get_workspace_root() -> Path:
    """Agent 工作区根目录，可通过 WORKSPACE_ROOT 覆盖。"""
    raw = os.getenv("WORKSPACE_ROOT", "").strip()
    if raw:
        return Path(raw).resolve()
    return _DEFAULT_WS.resolve()


def resolve_workspace_path(relative_path: str) -> Path:
    """
    将相对路径解析为 workspace 内绝对路径；禁止逃逸 workspace。
    """
    root = get_workspace_root()
    rel = relative_path.replace("\\", "/").lstrip("/")
    target = (root / rel).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"路径不允许访问 workspace 外: {relative_path}")
    return target
