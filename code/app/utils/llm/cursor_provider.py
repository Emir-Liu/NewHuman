"""Cursor 模型 LLM Provider（OpenAI 兼容接口）

官方 api.cursor.com 仅提供 Cloud Agents API（/v1/agents）与模型列表（/v1/models），
不提供通用 /v1/chat/completions。本 Provider 通过 langchain_openai.ChatOpenAI 连接
OpenAI 兼容端点，通常需配合本地代理（如 cursor-openai-api、cursor-api-proxy）。

凭证：LLM_MODEL_API_KEY 或 CURSOR_API_KEY（Cursor 惯例）。
可用模型：list_cursor_models() 或 cursor_sdk.Cursor.models.list()（需 cursor-sdk）。
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from config.llm_config import LLMConfig
from utils.llm.base import BaseLLMProvider
from utils.vllm_url import normalize_vllm_base_url

CURSOR_DEFAULT_MODEL = "composer-2.5"
CURSOR_MODELS_API_HOST = "https://api.cursor.com"


def resolve_cursor_base_url(config: LLMConfig) -> str:
    """解析 OpenAI 兼容 base_url（优先 LLM_MODEL_BASE_URL，其次 CURSOR_API_BASE_URL）。"""
    raw = (config.base_url or os.getenv("CURSOR_API_BASE_URL", "")).strip()
    return normalize_vllm_base_url(raw)


def resolve_cursor_api_key(config: LLMConfig) -> str:
    """解析 API Key（优先 LLM_MODEL_API_KEY，其次 CURSOR_API_KEY）。"""
    return (config.api_key or os.getenv("CURSOR_API_KEY", "")).strip()


def list_cursor_models(
    api_key: str | None = None,
    *,
    base_host: str | None = None,
    timeout: float = 15.0,
) -> list[str]:
    """
    查询账号可用的 Cursor 模型 ID（GET /v1/models）。

    不依赖 cursor-sdk；需有效 Cursor API Key。
    """
    key = (api_key or resolve_cursor_api_key(LLMConfig())).strip()
    if not key:
        raise ValueError("缺少 Cursor API Key（LLM_MODEL_API_KEY 或 CURSOR_API_KEY）")

    host = (base_host or os.getenv("CURSOR_API_BASE_URL") or CURSOR_MODELS_API_HOST).strip()
    host = host.rstrip("/")
    if host.endswith("/v1"):
        host = host[:-3]

    url = f"{host}/v1/models"
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        resp = client.get(url, auth=(key, ""))
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items") or data.get("models") or []
    ids: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
        elif isinstance(item, str):
            ids.append(item)
    return ids


class CursorLLMProvider(BaseLLMProvider):
    """
    通过 OpenAI 兼容 Chat Completions 接入 Cursor 模型。

    注意：官方 Cursor API 无直接 chat/completions；请配置指向兼容代理的 base_url。
    原生 tool calling 取决于上游代理是否支持；不支持时 llm_call 会走 JSON 兜底。
    """

    def get_llm(self) -> Any:
        from langchain_openai import ChatOpenAI

        config = self.config
        base_url = resolve_cursor_base_url(config)
        api_key = resolve_cursor_api_key(config)
        model_name = (config.model_name or CURSOR_DEFAULT_MODEL).strip()

        if not base_url:
            raise ValueError(
                "Cursor LLM 需要 OpenAI 兼容 base_url。"
                "请设置 LLM_MODEL_BASE_URL 或 CURSOR_API_BASE_URL"
                "（官方 api.cursor.com 无 /v1/chat/completions，通常指向本地代理）。"
            )
        if not api_key:
            raise ValueError(
                "Cursor LLM 需要 API Key。"
                "请设置 LLM_MODEL_API_KEY 或 CURSOR_API_KEY。"
            )

        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key,
            max_retries=5,
            streaming=False,
        )
