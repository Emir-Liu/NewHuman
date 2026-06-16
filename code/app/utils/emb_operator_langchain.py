"""
嵌入模型相关操作类 - LangChain 风格实现（兼容入口）

实现已迁移至 utils.embedding，此处保留原有 import 路径。
"""

from utils.embedding.operator import EmbOperator
from utils.embedding.factory import EmbeddingFactory
from utils.embedding.base import BaseEmbeddingProvider

__all__ = ["EmbOperator", "EmbeddingFactory", "BaseEmbeddingProvider"]


if __name__ == "__main__":
    from config.emb_config import EmbeddingConfig

    emb_config = EmbeddingConfig()
    emb = EmbOperator(emb_config)

    test_text = "这是一个测试文本"
    embedding = emb.embed_query(test_text)

    print(f"输入文本: {test_text}")
    print(f"向量维度: {len(embedding)}")
    print(f"向量前10维: {embedding[:10]}")

    print("\n=== 批量嵌入测试 ===")
    test_texts = [
        "这是第一个测试文本",
        "这是第二个测试文本",
        "这是第三个测试文本",
    ]
    embeddings = emb.embed_documents(test_texts)
    print(f"批量嵌入数量: {len(embeddings)}")
    for i, vec in enumerate(embeddings):
        print(f"  向量{i+1}维度: {len(vec)}")
