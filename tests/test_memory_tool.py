"""memory_tool 单元测试（无需 LLM）。"""

import sys
from datetime import date
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
def test_memory_append_and_search(ws):
    from func.graph.tools.memory_tool import memory_append, memory_read, memory_search

    out = memory_append.invoke({"note": "用户叫小明，喜欢咖啡", "target": "daily"})
    assert out.startswith("OK:")
    daily = f"memory/{date.today().isoformat()}.md"
    assert (ws / daily).is_file()

    read_out = memory_read.invoke({"path": daily})
    assert "小明" in read_out

    search_out = memory_search.invoke({"query": "小明", "max_results": 5})
    assert "小明" in search_out
    assert daily in search_out


@pytest.mark.smoke
def test_memory_update_summary(ws):
    from func.graph.tools.memory_tool import memory_read, memory_update_summary

    memory_update_summary.invoke({"content": "长期：用户偏好中文", "mode": "replace"})
    out = memory_read.invoke({"path": "MEMORY.md"})
    assert "中文" in out


@pytest.mark.smoke
def test_memory_read_list(ws):
    from func.graph.tools.memory_tool import memory_append, memory_read

    memory_append.invoke({"note": "测试条目", "target": "summary"})
    listing = memory_read.invoke({"path": ""})
    assert "MEMORY.md" in listing
