"""Workspace 初始化与安全读文件。"""

from __future__ import annotations

from pathlib import Path

from config.workspace_config import get_workspace_root, resolve_workspace_path

BOOTSTRAP_FILES = ("AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md")
MAX_BOOTSTRAP_BYTES = 8_192
SKILLS_DIR = "skills"


class WorkspaceManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or get_workspace_root()).resolve()

    def ensure_initialized(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "memory").mkdir(exist_ok=True)
        (self.root / SKILLS_DIR).mkdir(exist_ok=True)
        for name in BOOTSTRAP_FILES:
            path = self.root / name
            if not path.exists():
                path.write_text(f"# {name}\n\n(Template — run scripts/setup_workspace.ps1)\n", encoding="utf-8")
        return self.root

    def read_bootstrap(self, filename: str, *, max_bytes: int = MAX_BOOTSTRAP_BYTES) -> str:
        if filename not in BOOTSTRAP_FILES:
            return ""
        path = self.root / filename
        if not path.is_file():
            return ""
        raw = path.read_bytes()
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        return raw.decode("utf-8-sig", errors="replace")

    def read_all_bootstrap(self) -> dict[str, str]:
        self.ensure_initialized()
        return {name: self.read_bootstrap(name) for name in BOOTSTRAP_FILES if self.read_bootstrap(name)}

    def list_skills(self) -> list[dict[str, str]]:
        skills_root = self.root / SKILLS_DIR
        if not skills_root.is_dir():
            return []
        skills: list[dict[str, str]] = []
        for skill_dir in sorted(skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            rel = f"{SKILLS_DIR}/{skill_dir.name}/SKILL.md"
            desc = ""
            if skill_md.is_file():
                text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
                for line in text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        desc = line[:200]
                        break
                    if line.startswith("#"):
                        desc = line.lstrip("#").strip()[:200]
                        break
            skills.append({"name": skill_dir.name, "description": desc, "path": rel})
        return skills

    def safe_read(self, relative_path: str, *, max_bytes: int = MAX_BOOTSTRAP_BYTES) -> str:
        target = resolve_workspace_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError(relative_path)
        raw = target.read_bytes()
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        return raw.decode("utf-8-sig", errors="replace")


_default_manager: WorkspaceManager | None = None


def get_workspace_manager() -> WorkspaceManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = WorkspaceManager()
    return _default_manager
