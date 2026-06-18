"""工具层 smoke 测试（无需 LLM）。"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.smoke
def test_read_file_soul():
    import sys

    app_dir = REPO_ROOT / "code" / "app"
    sys.path.insert(0, str(app_dir))
    from func.graph.tools.file_tool import read_file

    content = read_file.invoke({"path": "SOUL.md"})
    assert "NewHuman" in content
    assert "Error" not in content[:20]
