"""Embedding 操作类（兼容门面）"""

from typing import List

from langchain_core.embeddings import Embeddings

from config.emb_config import EmbeddingConfig
from utils.embedding.factory import EmbeddingFactory


class EmbOperator:
    """
    嵌入模型操作类 - LangChain 风格接口

    支持的 API 类型由 EmbeddingFactory 注册表决定，默认：
    openai / bailian / deepseek / ollama / vllm
    """

    def __init__(self, embedding_config: EmbeddingConfig) -> None:
        self.config: EmbeddingConfig = embedding_config
        self.model_name = embedding_config.model
        self.api_key = embedding_config.api_key
        self.base_url = embedding_config.base_url
        self.api_type = embedding_config.api_type
        self.max_length = embedding_config.max_length

        self._provider = EmbeddingFactory.create(embedding_config)
        self.embeddings: Embeddings = self._provider.get_embeddings()

    def embed_query(self, text: str) -> List[float]:
        return self._provider.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._provider.embed_documents(texts)
