"""Embedding Provider 抽象基类"""

from abc import ABC, abstractmethod
from typing import List

from langchain_core.embeddings import Embeddings

from config.emb_config import EmbeddingConfig


class BaseEmbeddingProvider(ABC):
    """嵌入模型后端抽象基类"""

    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config

    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        """返回 LangChain Embeddings 实例"""

    def embed_query(self, text: str) -> List[float]:
        return self.get_embeddings().embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self.get_embeddings().embed_documents(texts)
