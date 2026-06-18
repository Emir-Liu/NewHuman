"""Smoke — 无需 LLM，验证环境与目录。"""

from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.smoke
def test_repo_layout():
    assert (REPO_ROOT / "code" / "app" / "main.py").is_file()
    assert (REPO_ROOT / "docs" / "0_需求文档" / "MVP需求文档_v1.0.md").is_file()


@pytest.mark.smoke
def test_workspace_templates_exist():
    ws = REPO_ROOT / "workspace" / "default"
    assert ws.is_dir(), "运行 scripts/setup_workspace.ps1 初始化 workspace"
    assert (ws / "SOUL.md").is_file()


@pytest.mark.smoke
def test_health_endpoint(base_url: str):
    try:
        r = httpx.get(f"{base_url}/health", timeout=5.0, trust_env=False)
    except httpx.HTTPError as e:
        pytest.skip(f"服务未启动: {e}")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


@pytest.mark.smoke
def test_home_page(base_url: str):
    try:
        r = httpx.get(f"{base_url}/", timeout=5.0, trust_env=False)
    except httpx.HTTPError:
        pytest.skip("服务未启动")
    assert r.status_code == 200
    assert "NewHuman" in r.text


@pytest.mark.smoke
def test_openapi_available(base_url: str):
    try:
        r = httpx.get(f"{base_url}/openapi.json", timeout=5.0)
    except httpx.HTTPError:
        pytest.skip("服务未启动")
    assert r.status_code == 200
    assert "paths" in r.json()


@pytest.mark.smoke
def test_capabilities_payload():
    import asyncio
    import sys

    sys.path.insert(0, str(REPO_ROOT / "code" / "app"))
    from api.v1.agent import get_capabilities

    data = asyncio.run(get_capabilities())
    names = {
        t["name"]
        for g in data.get("tool_groups", [])
        for t in g.get("tools", [])
    }
    assert "exec_powershell" in names
    assert "memory_search" in names
    assert "fetch_url" in names
    assert "delegate_subagent" in names
    assert "quick_prompts" in data
