"""vLLM 本地部署 LLM Provider（OpenAI 兼容接口）"""

from config.llm_config import LLMConfig
from utils.llm.base import BaseLLMProvider
from utils.vllm_url import normalize_vllm_base_url


class VLLMLLMProvider(BaseLLMProvider):
    """
    通过 langchain_openai.ChatOpenAI 接入 vLLM 服务

    vLLM 提供 OpenAI 兼容 API，Qwen 系列需关闭 thinking 模式。
    """

    def get_llm(self):
        from langchain_openai import ChatOpenAI

        config = self.config
        model_name = config.model_name
        low_model_name = model_name.lower().strip()

        kwargs = {
            "model": model_name,
            "base_url": normalize_vllm_base_url(config.base_url),
            "api_key": config.api_key,
            "max_retries": 5,
            "streaming": False,
        }

        if any(tag in low_model_name for tag in ("qwen3", "qwen2", "qwen25")):
            kwargs["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": False},
            }

        return ChatOpenAI(**kwargs)
