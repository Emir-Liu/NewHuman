"""read_lines / edit_lines 单元测试（无需 LLM）。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "code" / "app"


@pytest.fixture(autouse=True)
def _app_path():
    sys.path.insert(0, str(APP_DIR))
    yield


@pytest.fixture
def ws(tmp_path, monkeypatch):
    from config import workspace_config

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)
    return tmp_path


@pytest.mark.smoke
def test_read_lines_numbered_format(ws):
    from func.graph.tools.file_tool import read_lines, write_file

    write_file.invoke(
        {
            "path": "demo/lines.txt",
            "content": "alpha\nbeta\ngamma\ndelta\n",
        }
    )
    out = read_lines.invoke({"path": "demo/lines.txt", "start_line": 2, "end_line": 3})
    assert out.startswith("File:")
    assert "| beta" in out
    assert "| gamma" in out
    assert "   2 |" in out or " 2 |" in out


@pytest.mark.smoke
def test_edit_lines_replace_range(ws):
    from func.graph.tools.file_tool import edit_lines, read_lines, write_file

    write_file.invoke({"path": "x.txt", "content": "a\nb\nc\nd\n"})
    out = edit_lines.invoke(
        {
            "path": "x.txt",
            "start_line": 2,
            "end_line": 3,
            "new_content": "B\nC",
            "insert": False,
        }
    )
    assert out.startswith("OK:")
    read_out = read_lines.invoke({"path": "x.txt", "start_line": 1, "end_line": 0})
    assert "| a" in read_out
    assert "| B" in read_out
    assert "| C" in read_out
    assert "| d" in read_out
    assert "| b" not in read_out


@pytest.mark.smoke
def test_edit_lines_insert(ws):
    from func.graph.tools.file_tool import edit_lines, read_file, write_file

    write_file.invoke({"path": "y.txt", "content": "one\ntwo\n"})
    edit_lines.invoke(
        {
            "path": "y.txt",
            "start_line": 2,
            "end_line": 2,
            "new_content": "inserted",
            "insert": True,
        }
    )
    text = read_file.invoke({"path": "y.txt"})
    assert text == "one\ninserted\ntwo\n"


@pytest.mark.smoke
def test_read_lines_escape_workspace(ws):
    from func.graph.tools.file_tool import read_lines

    out = read_lines.invoke({"path": "../outside.txt", "start_line": 1})
    assert "Error:" in out
