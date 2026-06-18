"""M2 — Workspace 模板 + Context 注入 (TC-05)。"""

from pathlib import Path

import pytest

from conftest import post_chat_blocking, requires_llm

pytestmark = [pytest.mark.milestone_m2, pytest.mark.integration, requires_llm]

REPO_ROOT = Path(__file__).resolve().parent.parent
SOUL_PATH = REPO_ROOT / "workspace" / "default" / "SOUL.md"


@pytest.fixture
def english_soul():
    """临时将 SOUL 改为英文人格（测试后恢复）。"""
    original = SOUL_PATH.read_text(encoding="utf-8")
    SOUL_PATH.write_text(
        "# SOUL\n\nYou are a helpful assistant. Always reply in English only.\n",
        encoding="utf-8",
    )
    yield
    SOUL_PATH.write_text(original, encoding="utf-8")


def test_tc05_soul_language_english(api_client, english_soul):
    """TC-05: SOUL 为英文时，新 session 中文提问 → 英文回复。"""
    body = post_chat_blocking(api_client, "你好，请介绍一下你自己。")
    answer = body.get("answer", "") or ""
    has_english = any(c.isalpha() and ord(c) < 128 for c in answer)
    chinese_chars = sum(1 for c in answer if "\u4e00" <= c <= "\u9fff")
    assert has_english, f"期望英文回复: {answer[:200]}"
    assert chinese_chars < 5, f"回复含过多中文: {answer[:200]}"
