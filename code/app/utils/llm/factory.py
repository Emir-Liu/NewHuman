"""LLM Provider 工厂"""

from typing import Dict, Type

from config.llm_config import LLMConfig
from utils.llm.base import BaseLLMProvider
from utils.llm.openai_provider import OpenAILLMProvider
from utils.llm.ollama_provider import OllamaLLMProvider
from utils.llm.vllm_provider import VLLMLLMProvider


class LLMFactory:
    """
    LLM Provider 工厂

    根据 config.api_type 自动选择 Provider，支持 register() 扩展。

    使用示例:
        provider = LLMFactory.create(llm_config)
        llm = provider.get_llm()

    扩展方式:
        LLMFactory.register("azure", AzureLLMProvider)
    """

    _registry: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAILLMProvider,
        "bailian": OpenAILLMProvider,
        "ollama": OllamaLLMProvider,
        "vllm": VLLMLLMProvider,
    }

    @classmethod
    def register(cls, api_type: str, provider_cls: Type[BaseLLMProvider]) -> None:
        if not issubclass(provider_cls, BaseLLMProvider):
            raise TypeError(f"{provider_cls.__name__} 必须继承 BaseLLMProvider")
        cls._registry[api_type.lower()] = provider_cls

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMProvider:
        api_type = (config.api_type or "openai").lower()
        if api_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的 LLM api_type: '{api_type}'。可用类型: {available}"
            )
        return cls._registry[api_type](config)
