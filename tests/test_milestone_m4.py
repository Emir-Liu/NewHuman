"""M4 — memory 工具 + stop (TC-06, TC-07)。"""

import pytest

from conftest import post_chat_blocking, requires_llm

pytestmark = [pytest.mark.milestone_m4, pytest.mark.integration, requires_llm]


def test_tc07_memory_recall(api_client):
    """TC-07: 记住名字 → 新 session 回忆。"""
    post_chat_blocking(api_client, "请记住：我叫小明。")
    body = post_chat_blocking(api_client, "我叫什么名字？")
    answer = body.get("answer", "") or ""
    assert "小明" in answer, f"未从 MEMORY 召回: {answer[:200]}"


@pytest.mark.skip(reason="stop 需与 streaming task 联调 — M4 完成后启用")
def test_tc06_stop_generation(api_client):
    """TC-06: 长文本生成中 POST stop。"""
    pass
