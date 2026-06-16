"""Ollama 本地部署 Embedding Provider"""

from typing import List, Optional

from langchain_core.embeddings import Embeddings

from config.emb_config import EmbeddingConfig
from utils.embedding.base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """通过 langchain_ollama.OllamaEmbeddings 接入 Ollama"""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        self._embeddings: Optional[Embeddings] = None

    def _truncate_text(self, text: str) -> str:
        max_length = self.config.max_length
        if max_length and max_length > 0 and len(text) > max_length:
            return text[:max_length]
        return text

    def get_embeddings(self) -> Embeddings:
        if self._embeddings is None:
            from langchain_ollama import OllamaEmbeddings

            self._embeddings = OllamaEmbeddings(
                model=self.config.model,
                base_url=self.config.base_url,
            )
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        text = self._truncate_text(text)
        print(f"截断后文本: {text}\n截断后长度: {len(text)}")
        return self.get_embeddings().embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        texts = [self._truncate_text(t) for t in texts]
        return self.get_embeddings().embed_documents(texts)
