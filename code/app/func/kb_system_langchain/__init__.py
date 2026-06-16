"""
知识库系统 (kb_system)
======================

提供知识库的完整管理能力：
- models           数据模型 (Document, KnowledgeBaseInfo, DocumentInfo, ChunkInfo 等)
- interfaces       抽象接口 (BaseVectorStore, BaseMetadataStore, BaseKnowledgeBaseManager)
- vectordb         向量数据库适配器 (Chroma, Milvus)
- metadata_store   元数据存储适配器 (SQLAlchemy → SQLite/PG/MySQL)
- factories        工厂类 (VectorStoreFactory, MetadataStoreFactory, KBManagerFactory)
- document_loader  文档加载与分块
- kb_manager       知识库管理器实现（数据库无关）
- compat           向后兼容别名

新代码使用方式:
    from func.kb_system_langchain.factories import (
        VectorStoreFactory, MetadataStoreFactory, KBManagerFactory,
    )
    from func.kb_system_langchain.kb_manager import KnowledgeBaseManager, get_kb_manager
    from func.kb_system_langchain.models import KnowledgeBaseInfo, DocumentInfo, ChunkInfo
"""

from func.kb_system_langchain.models import (
    Document, SearchResult,
    KnowledgeBaseInfo, DocumentInfo, ChunkInfo,
)
from func.kb_system_langchain.interfaces import (
    BaseVectorStore, BaseMetadataStore, BaseKnowledgeBaseManager,
)
from func.kb_system_langchain.factories import (
    VectorStoreFactory, MetadataStoreFactory, KBManagerFactory,
)
from func.kb_system_langchain.vectordb.chroma import ChromaVectorStore
from func.kb_system_langchain.vectordb.milvus import MilvusVectorStore
from func.kb_system_langchain.document_loader import DocumentLoader, get_document_loader
from func.kb_system_langchain.document_processing import (
    ParserFactory,
    ChunkSplitterFactory,
)

__all__ = [
    # 数据模型
    "Document", "SearchResult",
    "KnowledgeBaseInfo", "DocumentInfo", "ChunkInfo",
    # 抽象接口
    "BaseVectorStore", "BaseMetadataStore", "BaseKnowledgeBaseManager",
    # 工厂
    "VectorStoreFactory", "MetadataStoreFactory", "KBManagerFactory",
    # 向量库适配器
    "ChromaVectorStore", "MilvusVectorStore",
    # 文档加载器
    "DocumentLoader", "get_document_loader",
    "ParserFactory", "ChunkSplitterFactory",
]
