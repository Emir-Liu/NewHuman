"""Embedding Provider 工厂"""

from typing import Dict, Type

from config.emb_config import EmbeddingConfig
from utils.embedding.base import BaseEmbeddingProvider
from utils.embedding.openai_provider import OpenAIEmbeddingProvider
from utils.embedding.ollama_provider import OllamaEmbeddingProvider
from utils.embedding.vllm_provider import VLLMEmbeddingProvider


class EmbeddingFactory:
    """
    Embedding Provider 工厂

    根据 config.api_type 自动选择 Provider，支持 register() 扩展。

    使用示例:
        provider = EmbeddingFactory.create(embedding_config)
        vec = provider.embed_query("文本")

    扩展方式:
        EmbeddingFactory.register("azure", AzureEmbeddingProvider)
    """

    _registry: Dict[str, Type[BaseEmbeddingProvider]] = {
        "openai": OpenAIEmbeddingProvider,
        "bailian": OpenAIEmbeddingProvider,
        "deepseek": OpenAIEmbeddingProvider,
        "ollama": OllamaEmbeddingProvider,
        "vllm": VLLMEmbeddingProvider,
    }

    @classmethod
    def register(cls, api_type: str, provider_cls: Type[BaseEmbeddingProvider]) -> None:
        if not issubclass(provider_cls, BaseEmbeddingProvider):
            raise TypeError(f"{provider_cls.__name__} 必须继承 BaseEmbeddingProvider")
        cls._registry[api_type.lower()] = provider_cls

    @classmethod
    def create(cls, config: EmbeddingConfig) -> BaseEmbeddingProvider:
        api_type = (config.api_type or "openai").lower()
        if api_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的 Embedding api_type: '{api_type}'。可用类型: {available}"
            )
        return cls._registry[api_type](config)
