"""
嵌入模型相关操作类 - LangChain 风格实现
提供统一的嵌入模型接口，支持多种API类型
"""

from typing import List, Optional
from langchain_core.embeddings import Embeddings


class EmbOperator:
    """
    嵌入模型操作类 - 完全使用 LangChain 风格接口

    支持的API类型：
    - openai: OpenAI 官方 API (通过 langchain-openai)
    - bailian: 阿里云百炼 API (兼容 OpenAI 接口)
    - deepseek: DeepSeek API (兼容 OpenAI 接口)
    - ollama: Ollama 本地部署 (通过 langchain-ollama)
    """

    def __init__(self, embedding_config) -> None:
        """
        初始化嵌入模型操作类

        Args:
            embedding_config: 嵌入模型配置对象
        """
        from config.emb_config import EmbeddingConfig
        
        self.config: EmbeddingConfig = embedding_config
        self.model_name = embedding_config.model
        self.api_key = embedding_config.api_key
        self.base_url = embedding_config.base_url
        self.api_type = embedding_config.api_type

        # 根据 api_type 创建对应的 LangChain Embeddings 实例
        self.embeddings: Embeddings = self._create_embeddings()

    def _create_embeddings(self) -> Embeddings:
        """
        创建对应类型的 LangChain Embeddings 实例
        
        Returns:
            Embeddings: LangChain 风格的嵌入模型实例
        """
        if self.api_type == 'ollama':
            # Ollama 本地部署
            from langchain_ollama import OllamaEmbeddings
            
            return OllamaEmbeddings(
                model=self.model_name,           # 模型名称，如 "nomic-embed-text"
                base_url=self.base_url or "http://localhost:11434",
            )
        
        elif self.api_type in ('openai', 'bailian', 'deepseek'):
            # OpenAI 风格接口（OpenAI、百炼、DeepSeek 等）
            from langchain_openai import OpenAIEmbeddings
            
            return OpenAIEmbeddings(
                model=self.model_name,           # 模型名称
                api_key=self.api_key,            # API 密钥
                base_url=self.base_url,          # 基础 URL
                # 可选：检查 API 密钥，Ollama 不需要，其他一般需要
                check_embedding_ctx_length=False,  # 禁用上下文长度检查（部分厂商不支持）
            )
        
        else:
            raise ValueError(f"不支持的 API 类型: {self.api_type}")

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单个查询文本
        
        Args:
            text: 要嵌入的文本字符串
        
        Returns:
            List[float]: 向量嵌入结果
        """
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文档（Chroma主要使用这个方法）
        
        Args:
            texts: 要嵌入的文本列表
        
        Returns:
            List[List[float]]: 向量嵌入结果列表
        """
        if not texts:
            return []
        
        return self.embeddings.embed_documents(texts)


if __name__ == '__main__':
    from config.emb_config import EmbeddingConfig
    
    emb_config = EmbeddingConfig()

    # 创建嵌入模型操作类
    emb = EmbOperator(emb_config)

    # 测试向量化
    test_text = "这是一个测试文本"
    embedding = emb.embed_query(test_text)

    print(f"输入文本: {test_text}")
    print(f"向量维度: {len(embedding)}")
    print(f"向量前10维: {embedding[:10]}")
    
    # 批量测试
    print("\n=== 批量嵌入测试 ===")
    test_texts = [
        "这是第一个测试文本",
        "这是第二个测试文本", 
        "这是第三个测试文本"
    ]
    embeddings = emb.embed_documents(test_texts)
    print(f"批量嵌入数量: {len(embeddings)}")
    for i, vec in enumerate(embeddings):
        print(f"  向量{i+1}维度: {len(vec)}")
