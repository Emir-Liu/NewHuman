"""
嵌入模型相关操作类
提供统一的嵌入模型接口，支持多种API类型
"""

from typing import List, Optional


from config.emb_config import EmbeddingConfig

class EmbOperator:
    """
    嵌入模型操作类

    支持的API类型：
    - openai: OpenAI 官方 API
    - bailian: 阿里云百炼 API
    - deepseek: DeepSeek API
    - 其他兼容 OpenAI 接口的服务
    """

    def __init__(self, embedding_config: EmbeddingConfig) -> None:
        """
        初始化嵌入模型操作类

        Args:
            embedding_config: 嵌入模型配置对象，如果为None则使用默认配置
        """

        self.config = embedding_config
        self.model_name = embedding_config.model
        self.api_key = embedding_config.api_key
        self.base_url = embedding_config.base_url
        self.api_type = embedding_config.api_type

        if self.api_type == 'bailian':
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def embed_query(self, text: str) -> list[float]:
        """嵌入单个查询文本"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=[text]  # 注意：需要包装成列表
        )
        return response.data[0].embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档（Chroma主要使用这个方法）"""
        if not texts:
            return []
        
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in response.data]

if __name__ == '__main__':
    emb_config = EmbeddingConfig()

    # 创建嵌入模型操作类
    emb = EmbOperator(emb_config)

    # 测试向量化
    test_text = "这是一个测试文本"
    embedding = emb.embed_query(test_text)

    print(f"输入文本: {test_text}")
    print(f"向量维度: {len(embedding)}")
    print(f"向量前10维: {embedding[:10]}")
