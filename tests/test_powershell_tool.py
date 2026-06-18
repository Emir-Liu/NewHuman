"""exec_powershell 单元测试（无需 LLM）。"""

import pytest

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.mark.smoke
def test_exec_powershell_python_version():
    import sys

    sys.path.insert(0, str(REPO_ROOT / "code" / "app"))
    from func.graph.tools.powershell_tool import run_powershell

    out = run_powershell("python --version")
    assert "exit_code:" in out
    assert "Python" in out or "python" in out.lower()


@pytest.mark.smoke
def test_exec_powershell_list_dir():
    import sys

    sys.path.insert(0, str(REPO_ROOT / "code" / "app"))
    from func.graph.tools.powershell_tool import run_powershell

    out = run_powershell("Get-ChildItem -Name")
    assert "exit_code: 0" in out
    assert "SOUL.md" in out or "stdout:" in out


@pytest.mark.smoke
def test_tool_registered():
    import sys

    sys.path.insert(0, str(REPO_ROOT / "code" / "app"))
    from func.graph.tools.tool_registry import tools_by_name

    assert "exec_powershell" in tools_by_name
