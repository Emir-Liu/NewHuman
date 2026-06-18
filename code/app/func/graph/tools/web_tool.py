"""网络访问工具 — 抓取 URL 正文供 LLM 阅读。"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool

DEFAULT_TIMEOUT_SEC = float(os.getenv("FETCH_URL_TIMEOUT", "15"))
MAX_BYTES = int(os.getenv("FETCH_URL_MAX_BYTES", "524288"))
USER_AGENT = "NewHuman/1.0 (+https://github.com/newhuman)"


class _TextExtractor(HTMLParser):
    """简单 HTML → 纯文本。"""

    _SKIP_TAGS = frozenset({"script", "style", "noscript", "head"})

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip())

    def get_text(self) -> str:
        raw = "\n".join(self._chunks)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
    text = parser.get_text()
    return text or re.sub(r"<[^>]+>", " ", html)


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
        return True
    if ip.is_multicast:
        return True
    return False


def _validate_url(url: str) -> tuple[str, str]:
    """返回 (normalized_url, hostname) 或抛出 ValueError。"""
    raw = (url or "").strip()
    if not raw:
        raise ValueError("URL 不能为空")
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅允许 http/https URL")
    if not parsed.netloc:
        raise ValueError("无效的 URL")
    host = parsed.hostname
    if not host:
        raise ValueError("无效的 URL")
    lower = host.lower()
    if lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError("禁止访问 localhost")
    if lower.endswith(".local") or lower.endswith(".internal"):
        raise ValueError("禁止访问内网域名")

    try:
        for info in socket.getaddrinfo(host, None):
            addr = info[4][0]
            if _is_private_ip(addr):
                raise ValueError(f"禁止访问私有/内网地址: {host}")
    except socket.gaierror as e:
        raise ValueError(f"无法解析域名 {host}: {e}") from e

    return raw, host


def fetch_url_content(url: str, *, timeout_sec: float | None = None) -> str:
    """抓取 URL 并返回可读文本（供单元测试直接调用）。"""
    timeout = timeout_sec if timeout_sec is not None else DEFAULT_TIMEOUT_SEC
    try:
        normalized, _host = _validate_url(url)
    except ValueError as e:
        return f"Error: {e}"

    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain,*/*"}
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            trust_env=False,
        ) as client:
            resp = client.get(normalized, headers=headers)
    except httpx.TimeoutException:
        return f"Error: 请求超时（{timeout}s）"
    except httpx.HTTPError as e:
        return f"Error: HTTP 请求失败: {e}"

    if resp.status_code >= 400:
        return f"Error: HTTP {resp.status_code} for {normalized}"

    raw = resp.content[:MAX_BYTES]
    charset = resp.encoding or "utf-8"
    try:
        body = raw.decode(charset, errors="replace")
    except LookupError:
        body = raw.decode("utf-8", errors="replace")

    content_type = (resp.headers.get("content-type") or "").lower()
    if "html" in content_type or "<html" in body.lower()[:500]:
        text = _html_to_text(body)
    else:
        text = body.strip()

    if not text:
        return f"Error: 未能从 {normalized} 提取可读文本"

    truncated = len(resp.content) > MAX_BYTES
    meta = f"URL: {normalized}\nStatus: {resp.status_code}\nLength: {len(text)} chars"
    if truncated:
        meta += f" (响应已截断至 {MAX_BYTES} bytes)"
    return f"{meta}\n\n---\n\n{text}"


@tool
def fetch_url(url: str) -> str:
    """抓取 http/https 网页并返回提取后的纯文本（供阅读与总结）。

    禁止 file://、localhost 及内网地址。响应过大时会截断。

    Args:
        url: 完整 URL，例如 https://example.com
    """
    return fetch_url_content(url)
