"""web_tool 单元测试（无需 LLM，需网络）。"""

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
def test_fetch_url_blocks_localhost():
    from func.graph.tools.web_tool import fetch_url_content

    out = fetch_url_content("http://127.0.0.1/")
    assert "Error:" in out
    assert "localhost" in out.lower() or "禁止" in out


@pytest.mark.smoke
def test_fetch_url_blocks_file_scheme():
    from func.graph.tools.web_tool import fetch_url_content

    out = fetch_url_content("file:///etc/passwd")
    assert "Error:" in out


@pytest.mark.smoke
def test_fetch_url_example_com():
    from func.graph.tools.web_tool import fetch_url_content

    out = fetch_url_content("https://example.com")
    if "Error:" in out and "超时" in out:
        pytest.skip("网络不可用或超时")
    assert "example" in out.lower()
    assert "Error:" not in out.split("\n")[0]
