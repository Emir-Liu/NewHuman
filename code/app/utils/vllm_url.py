"""vLLM OpenAI 兼容接口 URL 工具"""


def normalize_vllm_base_url(base_url: str) -> str:
    """
    规范化 vLLM base_url，确保 OpenAI 客户端请求 /v1/chat/completions。

    配置示例:
        http://192.168.0.10:12302        -> http://192.168.0.10:12302/v1
        http://192.168.0.10:12302/       -> http://192.168.0.10:12302/v1
        http://192.168.0.10:12302/v1     -> http://192.168.0.10:12302/v1
        http://192.168.0.10:12302/v1/    -> http://192.168.0.10:12302/v1
    """
    url = (base_url or "").strip().rstrip("/")
    if not url:
        return url
    if not url.endswith("/v1"):
        url = f"{url}/v1"
    return url
