"""conversation_memory 单元测试（无需 LLM）。"""

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
    from config import agent_config, workspace_config

    monkeypatch.setattr(workspace_config, "_DEFAULT_WS", tmp_path)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)
    monkeypatch.setenv("CONVERSATION_MEMORY_ENABLED", "true")
    agent_config._agent_config = None
    yield tmp_path
    agent_config._agent_config = None


@pytest.mark.smoke
def test_save_conversation_turn_creates_daily_file(ws):
    from func.graph.conversation_memory import save_conversation_turn
    from func.graph.tools.memory_tool import memory_search

    save_conversation_turn("conv-abc", "你好", "你好，有什么可以帮你？")

    daily = f"memory/conversations/{date.today().isoformat()}.md"
    path = ws / daily
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "conv-abc" in text
    assert "### User" in text
    assert "你好" in text
    assert "### Assistant" in text

    search_out = memory_search.invoke({"query": "conv-abc", "max_results": 5})
    assert daily.replace("/", "\\") in search_out or daily in search_out


@pytest.mark.smoke
def test_save_conversation_disabled(ws, monkeypatch):
    from config import agent_config
    from func.graph.conversation_memory import save_conversation_turn

    monkeypatch.setenv("CONVERSATION_MEMORY_ENABLED", "false")
    agent_config._agent_config = None

    save_conversation_turn("conv-x", "hi", "hello")
    assert not any(ws.rglob("*.md"))

    agent_config._agent_config = None
