"""Workspace / Context 单元测试（无需 LLM）。"""

import pytest

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.mark.smoke
def test_context_assembler_bootstrap():
    import sys

    app_dir = REPO_ROOT / "code" / "app"
    sys.path.insert(0, str(app_dir))
    from func.graph.workspace.context_assembler import ContextAssembler
    from langchain_core.messages import SystemMessage

    asm = ContextAssembler()
    msg = asm.assemble(include_bootstrap=True)
    assert isinstance(msg, SystemMessage)
    assert "NewHuman" in msg.content
    assert "SOUL.md" in msg.content or "SOUL" in msg.content


@pytest.mark.smoke
def test_context_assembler_skills_index():
    import sys

    app_dir = REPO_ROOT / "code" / "app"
    sys.path.insert(0, str(app_dir))
    from func.graph.workspace.context_assembler import ContextAssembler

    asm = ContextAssembler()
    msg = asm.assemble(include_bootstrap=False)
    assert "kb-qa" in msg.content or "Skills" in msg.content
