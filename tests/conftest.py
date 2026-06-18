"""MVP 验收测试 — 公共 fixtures 与 helpers。"""

from __future__ import annotations

import os
import re

import httpx
import pytest

TEST_USER = os.getenv("TEST_USER", "mvp-test-user")


def get_base_url() -> str:
    return os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def llm_configured() -> bool:
    """检查 .env 中 LLM 是否已配置（非 demo 占位符）。"""
    env_path = os.path.join(
        os.path.dirname(__file__), "..", "code", "app", ".env"
    )
    if not os.path.isfile(env_path):
        return False
    with open(env_path, encoding="utf-8") as f:
        content = f.read()
    placeholders = ("xxx", "sk-xxx", "your_", "changeme")
    for key in ("LLM_MODEL_NAME", "LLM_MODEL_BASE_URL", "LLM_MODEL_API_KEY"):
        m = re.search(rf"^{key}=(.+)$", content, re.MULTILINE)
        if not m:
            return False
        val = m.group(1).strip().strip('"').strip("'")
        if not val or any(p in val.lower() for p in placeholders):
            return False
    return True


def _server_up() -> bool:
    try:
        return httpx.get(f"{get_base_url()}/health", timeout=15.0, trust_env=False).is_success
    except httpx.HTTPError:
        return False


@pytest.fixture(scope="session")
def base_url() -> str:
    return get_base_url()


@pytest.fixture
def api_client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=120.0, trust_env=False) as client:
        yield client


@pytest.fixture(scope="session")
def server_available(base_url: str) -> bool:
    try:
        r = httpx.get(f"{base_url}/health", timeout=5.0, trust_env=False)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except (httpx.HTTPError, ValueError):
        return False


requires_llm = pytest.mark.skipif(
    not llm_configured(),
    reason="LLM 未配置，请编辑 code/app/.env",
)


@pytest.fixture(autouse=True)
def _require_server_for_integration(request, base_url):
    if "integration" not in request.keywords:
        return
    last_err = None
    for _ in range(3):
        try:
            if httpx.get(f"{base_url}/health", timeout=15.0, trust_env=False).is_success:
                return
        except httpx.HTTPError as e:
            last_err = e
    pytest.skip(f"API 未启动: {base_url} ({last_err})")


def post_chat_stream(
    client: httpx.Client,
    query: str,
    *,
    conversation_id: str = "",
) -> tuple[str, list[str]]:
    """POST streaming 并收集 SSE 事件文本。"""
    payload = {
        "query": query,
        "response_mode": "streaming",
        "conversation_id": conversation_id,
        "user": TEST_USER,
        "inputs": {},
    }
    events: list[str] = []
    full_text = ""

    with client.stream("POST", "/v1/chat-messages", json=payload) as resp:
        assert resp.status_code == 200, resp.text
        for line in resp.iter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                events.append(chunk)
                if '"answer"' in chunk or '"event"' in chunk:
                    full_text += chunk

    return full_text, events


def post_chat_blocking(
    client: httpx.Client,
    query: str,
    *,
    conversation_id: str = "",
) -> dict:
    payload = {
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": TEST_USER,
        "inputs": {},
    }
    r = client.post("/v1/chat-messages", json=payload)
    assert r.status_code == 200, r.text
    return r.json()
