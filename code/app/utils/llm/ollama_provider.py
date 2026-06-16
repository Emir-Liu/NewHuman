"""Ollama 本地部署 LLM Provider"""

from config.llm_config import LLMConfig
from utils.llm.base import BaseLLMProvider


class OllamaLLMProvider(BaseLLMProvider):
    """通过 langchain_ollama.ChatOllama 接入 Ollama"""

    def get_llm(self):
        from langchain_ollama import ChatOllama

        config = self.config
        low_model_name = config.model_name.lower().strip()
        streaming = "qwen3" in low_model_name

        return ChatOllama(
            model=config.model_name,
            base_url=config.base_url,
            api_key=config.api_key,
            streaming=streaming,
            max_retries=5,
        )
