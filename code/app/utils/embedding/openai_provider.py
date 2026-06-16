"""OpenAI 兼容接口 Embedding Provider（openai / bailian / deepseek）"""

from typing import Optional

from langchain_core.embeddings import Embeddings

from config.emb_config import EmbeddingConfig
from utils.embedding.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """通过 langchain_openai.OpenAIEmbeddings 接入 OpenAI 兼容服务"""

    def __init__(self, config: EmbeddingConfig) -> None:
        super().__init__(config)
        self._embeddings: Optional[Embeddings] = None

    def get_embeddings(self) -> Embeddings:
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                check_embedding_ctx_length=False,
            )
        return self._embeddings
