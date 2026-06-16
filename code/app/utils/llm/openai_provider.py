"""OpenAI 兼容接口 LLM Provider（openai / bailian 等）"""

from config.llm_config import LLMConfig
from utils.llm.base import BaseLLMProvider


class OpenAILLMProvider(BaseLLMProvider):
    """通过 langchain_openai.ChatOpenAI 接入 OpenAI 兼容服务"""

    def get_llm(self):
        from langchain_openai import ChatOpenAI

        config = self.config
        model_name = config.model_name
        low_model_name = model_name.lower().strip()
        api_type = (config.api_type or "openai").lower()

        kwargs = {
            "model": model_name,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "max_retries": 5,
        }

        if "qwen3" in low_model_name:
            if api_type == "openai":
                kwargs["streaming"] = False
                kwargs["extra_body"] = {
                    "chat_template_kwargs": {"enable_thinking": False},
                }
            elif api_type == "bailian":
                kwargs["streaming"] = True
            else:
                kwargs["streaming"] = False
        else:
            kwargs["streaming"] = False

        return ChatOpenAI(**kwargs)
