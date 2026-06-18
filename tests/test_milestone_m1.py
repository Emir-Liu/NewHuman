"""M1 — ReAct 图 + read_file + 流式 (TC-01, TC-02)。"""

import pytest

from conftest import post_chat_blocking, post_chat_stream, requires_llm

pytestmark = [pytest.mark.milestone_m1, pytest.mark.integration, requires_llm]


def test_tc01_streaming_hello(api_client):
    """TC-01: POST streaming「你好」→ 收到 SSE 事件。"""
    text, events = post_chat_stream(api_client, "你好")
    assert len(events) >= 1, "应收到至少一条 SSE data 事件"
    combined = " ".join(events)
    assert "error" not in combined.lower() or "event" in combined


def test_tc02_read_soul_md(api_client):
    """TC-02: 读取 SOUL.md 并总结 → 应答含人格/助手相关内容。"""
    body = post_chat_blocking(
        api_client,
        "请使用 read_file 读取 SOUL.md，并用一句话总结其内容。",
    )
    answer = body.get("answer", "") or str(body)
    assert len(answer) > 10
    keywords = ("助手", "NewHuman", "SOUL", "人格", "工具", "简洁", "准确", "专业")
    assert any(k.lower() in answer.lower() for k in keywords), (
        f"回答未体现 SOUL.md 内容: {answer[:200]}"
    )
