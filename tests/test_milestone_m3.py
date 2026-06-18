"""M3 — search_knowledge + exec + web (TC-03, TC-08~10)。"""

import pytest

from conftest import post_chat_blocking, requires_llm

pytestmark = [pytest.mark.milestone_m3, pytest.mark.integration, requires_llm]


@pytest.mark.skip(reason="需预先上传 KB 文档并配置 collection — 实现 M3 后启用")
def test_tc03_knowledge_qa(api_client):
    """TC-03: 根据知识库文档回答。"""
    body = post_chat_blocking(api_client, "根据文档，XX 是什么？")
    answer = body.get("answer", "")
    assert len(answer) > 20


def test_tc08_exec_python_version(api_client):
    """TC-08: exec python --version。"""
    body = post_chat_blocking(
        api_client,
        "请使用 exec_powershell 在 workspace 里执行 python --version 并告诉我输出结果。",
    )
    answer = body.get("answer", "") or ""
    assert "python" in answer.lower() or "Python" in answer


@pytest.mark.skip(reason="需配置 web_search API — 实现 web_tool 后启用")
def test_tc09_web_search(api_client):
    """TC-09: web_search Python 3.12 新特性。"""
    body = post_chat_blocking(api_client, "搜索 Python 3.12 新特性并摘要")
    answer = body.get("answer", "")
    assert "http" in answer.lower() or "3.12" in answer


@pytest.mark.skip(reason="需实现 web_fetch — M3 完成后启用")
def test_tc10_web_fetch(api_client):
    """TC-10: web_fetch example.com。"""
    body = post_chat_blocking(
        api_client,
        "抓取 https://example.com 并用一句话总结页面内容。",
    )
    answer = body.get("answer", "")
    assert "example" in answer.lower()
