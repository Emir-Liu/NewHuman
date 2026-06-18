"""file_tool 单元测试（无需 LLM）。"""

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
def test_edit_file_search_replace(tmp_path, monkeypatch):
    from config import workspace_config
    from func.graph.tools.file_tool import edit_file, write_file

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    write_file.invoke({"path": "demo/a.txt", "content": "hello world\nhello again\n"})
    out = edit_file.invoke(
        {
            "path": "demo/a.txt",
            "old_string": "hello world",
            "new_string": "hi world",
            "replace_all": False,
        }
    )
    assert out.startswith("OK:")
    text = (tmp_path / "demo" / "a.txt").read_text(encoding="utf-8")
    assert "hi world" in text
    assert "hello world" not in text
    assert "hello again" in text


@pytest.mark.smoke
def test_edit_file_multiple_match_requires_replace_all(tmp_path, monkeypatch):
    from config import workspace_config
    from func.graph.tools.file_tool import edit_file, write_file

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    write_file.invoke({"path": "x.txt", "content": "aa aa aa"})
    out = edit_file.invoke(
        {"path": "x.txt", "old_string": "aa", "new_string": "b", "replace_all": False}
    )
    assert "Error:" in out and "匹配" in out


@pytest.mark.smoke
def test_edit_file_escape_workspace(tmp_path, monkeypatch):
    from config import workspace_config
    from func.graph.tools.file_tool import edit_file

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    out = edit_file.invoke(
        {
            "path": "../outside.txt",
            "old_string": "a",
            "new_string": "b",
            "replace_all": False,
        }
    )
    assert "Error:" in out
