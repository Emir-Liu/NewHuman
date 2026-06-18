"""delegate_subagent / list_agent_roles 单元测试（无需 LLM）。"""

from __future__ import annotations

import asyncio
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
def test_subagent_tools_registered():
    from func.graph.tools.tool_registry import get_allowed_tool_names, is_tool_allowed

    names = get_allowed_tool_names()
    assert "delegate_subagent" in names
    assert "list_agent_roles" in names
    assert is_tool_allowed("delegate_subagent")


@pytest.mark.smoke
def test_list_agent_roles_returns_presets():
    from func.graph.tools.subagent_tool import list_agent_roles

    raw = list_agent_roles.invoke({})
    assert "researcher" in raw
    assert "coder" in raw


@pytest.mark.smoke
def test_delegate_subagent_rejects_empty_task():
    from func.graph.tools.subagent_tool import delegate_subagent

    out = asyncio.run(delegate_subagent.ainvoke({"task": "", "role": "", "context": ""}))
    assert "Error:" in out and "task" in out.lower()


@pytest.mark.smoke
def test_subagent_tools_hidden_at_depth():
    from func.graph.tools.subagent_context import subagent_depth_scope
    from func.graph.tools.tool_registry import get_allowed_tool_names

    assert "delegate_subagent" in get_allowed_tool_names()
    with subagent_depth_scope():
        names = get_allowed_tool_names()
        assert "delegate_subagent" not in names
        assert "list_agent_roles" in names


@pytest.mark.smoke
def test_delegate_subagent_depth_limit(monkeypatch):
    from func.graph.tools import subagent_tool
    from func.graph.tools.subagent_context import subagent_depth_scope
    from func.graph.tools.subagent_tool import delegate_subagent

    async def _fake_graph(_msg: str) -> str:
        return "子任务完成"

    monkeypatch.setattr(subagent_tool, "_invoke_subagent_graph", _fake_graph)

    with subagent_depth_scope():
        out = asyncio.run(
            delegate_subagent.ainvoke(
                {"task": "应被拒绝", "role": "researcher", "context": ""}
            )
        )
    assert "Error:" in out and "深度" in out


@pytest.mark.smoke
def test_delegate_subagent_mock_success(monkeypatch):
    from func.graph.tools import subagent_tool
    from func.graph.tools.subagent_tool import delegate_subagent

    calls: list[str] = []

    async def _fake_graph(msg: str) -> str:
        calls.append(msg)
        return "调研结论：方案可行"

    monkeypatch.setattr(subagent_tool, "_invoke_subagent_graph", _fake_graph)

    out = asyncio.run(
        delegate_subagent.ainvoke(
            {
                "task": "调研 FastAPI 性能",
                "role": "researcher",
                "context": "用于技术选型",
            }
        )
    )
    assert out == "调研结论：方案可行"
    assert calls and "调研 FastAPI 性能" in calls[0]
    assert "researcher" in calls[0]
