"""Workspace / Context 单元测试（无需 LLM）。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "code" / "app"


@pytest.fixture(autouse=True)
def _app_path():
    sys.path.insert(0, str(APP_DIR))
    yield


@pytest.mark.smoke
def test_context_assembler_bootstrap():
    from func.graph.workspace.context_assembler import ContextAssembler
    from langchain_core.messages import SystemMessage

    asm = ContextAssembler()
    msg = asm.assemble(include_bootstrap=True)
    assert isinstance(msg, SystemMessage)
    assert "NewHuman" in msg.content
    assert "SOUL.md" in msg.content or "SOUL" in msg.content


@pytest.mark.smoke
def test_context_assembler_skills_index():
    from func.graph.workspace.context_assembler import ContextAssembler

    asm = ContextAssembler()
    msg = asm.assemble(include_bootstrap=False)
    assert "skill-creator" in msg.content or "kb-qa" in msg.content
    assert "Get-Content" in msg.content or "exec_powershell" in msg.content
    assert "skills/" in msg.content


@pytest.mark.smoke
def test_list_skills(tmp_path, monkeypatch):
    from config import workspace_config
    from func.graph.workspace.manager import WorkspaceManager

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    skill_dir = tmp_path / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# demo-skill\n\n用于测试的技能摘要。\n",
        encoding="utf-8",
    )

    mgr = WorkspaceManager(root=tmp_path)
    skills = mgr.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "demo-skill"
    assert "测试" in skills[0]["description"]
    assert skills[0]["path"] == "skills/demo-skill/SKILL.md"


@pytest.mark.smoke
def test_read_skill_via_read_file(tmp_path, monkeypatch):
    from config import workspace_config
    from func.graph.tools.file_tool import read_file

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    skill_md = tmp_path / "skills" / "my-skill" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text("# my-skill\n\n内容\n", encoding="utf-8")

    content = read_file.invoke({"path": "skills/my-skill/SKILL.md"})
    assert "my-skill" in content
    assert "Error" not in content[:20]

    blocked = read_file.invoke({"path": "../outside/SKILL.md"})
    assert "Error:" in blocked


@pytest.mark.smoke
def test_skills_usage_notes_in_prompt():
    from func.graph.tools.tool_registry import format_tools_usage_notes

    notes = format_tools_usage_notes()
    assert "skills/" in notes
    assert "skill-creator" in notes
