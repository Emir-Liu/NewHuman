"""M5 — 多轮对话等收尾验收 (TC-04)。"""

import pytest

from conftest import post_chat_blocking, requires_llm

pytestmark = [pytest.mark.milestone_m5, pytest.mark.integration, requires_llm]


def test_tc04_multi_turn_coreference(api_client):
    """TC-04: 同 conversation_id 两轮追问，第二轮理解指代。"""
    r1 = post_chat_blocking(
        api_client,
        "我最喜欢的编程语言是 Python。",
    )
    conv_id = r1.get("conversation_id") or ""
    assert conv_id, "第一轮应返回 conversation_id"

    r2 = post_chat_blocking(
        api_client,
        "它有哪些优点？",
        conversation_id=conv_id,
    )
    answer = r2.get("answer", "") or ""
    assert "python" in answer.lower() or "Python" in answer, (
        f"第二轮未理解指代: {answer[:300]}"
    )
