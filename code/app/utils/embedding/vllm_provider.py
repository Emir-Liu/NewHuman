"""vLLM 本地部署 Embedding Provider（OpenAI 兼容接口）"""

from typing import List, Optional

from langchain_core.embeddings import Embeddings

from config.emb_config import EmbeddingConfig
from utils.embedding.base import BaseEmbeddingProvider
from utils.vllm_url import normalize_vllm_base_url


class VLLMEmbeddingProvider(BaseEmbeddingProvider):
    """
    通过 langchain_openai.OpenAIEmbeddings 接入 vLLM Embedding 服务

    vLLM 提供 OpenAI 兼容 /v1/embeddings 接口。
    """

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
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=normalize_vllm_base_url(self.config.base_url),
                check_embedding_ctx_length=False,
            )
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        text = self._truncate_text(text)
        return self.get_embeddings().embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        texts = [self._truncate_text(t) for t in texts]
        return self.get_embeddings().embed_documents(texts)
