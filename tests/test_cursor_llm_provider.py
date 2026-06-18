"""Cursor LLM Provider 冒烟测试（无真实 API 调用）。"""

import pytest

from config.llm_config import LLMConfig
from utils.llm.cursor_provider import (
    CursorLLMProvider,
    resolve_cursor_api_key,
    resolve_cursor_base_url,
)
from utils.llm.factory import LLMFactory


@pytest.mark.smoke
def test_factory_creates_cursor_provider(monkeypatch):
    monkeypatch.setenv("LLM_MODEL_API_TYPE", "cursor")
    monkeypatch.setenv("LLM_MODEL_API_KEY", "cursor_test_key")
    monkeypatch.setenv("LLM_MODEL_NAME", "composer-2.5")
    monkeypatch.setenv("LLM_MODEL_BASE_URL", "http://127.0.0.1:8765/v1")

    config = LLMConfig()
    provider = LLMFactory.create(config)

    assert isinstance(provider, CursorLLMProvider)


@pytest.mark.smoke
def test_cursor_api_key_fallback(monkeypatch):
    monkeypatch.delenv("LLM_MODEL_API_KEY", raising=False)
    monkeypatch.setenv("CURSOR_API_KEY", "cursor_fallback_key")
    monkeypatch.setenv("LLM_MODEL_API_TYPE", "cursor")
    monkeypatch.setenv("LLM_MODEL_BASE_URL", "http://localhost:8080")

    config = LLMConfig()
    assert config.api_key == "cursor_fallback_key"
    assert resolve_cursor_api_key(config) == "cursor_fallback_key"
    assert resolve_cursor_base_url(config) == "http://localhost:8080/v1"


@pytest.mark.smoke
def test_cursor_provider_builds_chat_openai(monkeypatch):
    monkeypatch.setenv("LLM_MODEL_API_TYPE", "cursor")
    monkeypatch.setenv("LLM_MODEL_API_KEY", "cursor_test_key")
    monkeypatch.setenv("LLM_MODEL_NAME", "composer-2.5")
    monkeypatch.setenv("LLM_MODEL_BASE_URL", "http://127.0.0.1:8765/v1")

    llm = LLMFactory.create(LLMConfig()).get_llm()

    assert llm.model_name == "composer-2.5"
    assert getattr(llm, "streaming", None) is False
    assert hasattr(llm, "bind_tools")


@pytest.mark.smoke
def test_cursor_provider_requires_base_url(monkeypatch):
    monkeypatch.setenv("LLM_MODEL_API_TYPE", "cursor")
    monkeypatch.setenv("LLM_MODEL_API_KEY", "cursor_test_key")
    monkeypatch.delenv("LLM_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("CURSOR_API_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="base_url"):
        LLMFactory.create(LLMConfig()).get_llm()
