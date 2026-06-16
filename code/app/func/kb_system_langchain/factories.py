"""
知识库系统工厂
VectorStoreFactory  —— 向量库实例工厂
MetadataStoreFactory —— 元数据存储工厂
KBManagerFactory     —— 知识库管理器工厂
"""

from typing import Dict, Type, Optional

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from func.kb_system_langchain.interfaces import BaseVectorStore, BaseMetadataStore, BaseKnowledgeBaseManager
from func.kb_system_langchain.vectordb.chroma import ChromaVectorStore
from func.kb_system_langchain.vectordb.milvus import MilvusVectorStore


class VectorStoreFactory:
    """
    向量库工厂

    内置注册 chroma / milvus 两种适配器，支持运行时通过 register() 扩展。

    使用示例:
        store = VectorStoreFactory.create("chroma", vectordb_config, emb_config)
        store = VectorStoreFactory.create("milvus", vectordb_config, emb_config)

    扩展方式:
        VectorStoreFactory.register("faiss", FAISSVectorStore)
    """

    # 注册表：{store_type: StoreClass}
    _registry: Dict[str, Type[BaseVectorStore]] = {
        "chroma": ChromaVectorStore,
        "milvus": MilvusVectorStore,
    }

    @classmethod
    def register(cls, store_type: str, store_cls: Type[BaseVectorStore]) -> None:
        """
        注册新的向量库类型

        Args:
            store_type: 类型名称（如 "faiss", "qdrant"）
            store_cls:  实现了 BaseVectorStore 的类

        示例:
            VectorStoreFactory.register("faiss", FAISSVectorStore)
        """
        if not issubclass(store_cls, BaseVectorStore):
            raise TypeError(f"{store_cls.__name__} 必须继承 BaseVectorStore")
        cls._registry[store_type.lower()] = store_cls
        # print(f"[VectorStoreFactory] 注册向量库类型: {store_type} -> {store_cls.__name__}")

    @classmethod
    def create(
        cls,
        store_type: str,
        vectordb_config: VectorDBConfig,
        embedding_config: EmbeddingConfig,
    ) -> BaseVectorStore:
        """
        创建向量库实例

        Args:
            store_type:        向量库类型 (chroma / milvus / ...)
            vectordb_config:   向量数据库配置
            embedding_config:  嵌入模型配置

        Returns:
            BaseVectorStore: 向量库实例

        Raises:
            ValueError: 不支持的向量库类型
        """
        store_type = store_type.lower()

        if store_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的向量库类型: '{store_type}'。可用类型: {available}"
            )

        store_cls = cls._registry[store_type]

        try:
            instance = store_cls(
                vectordb_config=vectordb_config,
                embedding_config=embedding_config,
            )
            # print(f"[VectorStoreFactory] 创建 {store_cls.__name__} 成功")
            return instance
        except Exception as e:
            raise RuntimeError(
                f"创建向量库实例失败 [{store_type}]: {e}"
            ) from e

    @classmethod
    def list_registered(cls) -> Dict[str, str]:
        """列出所有已注册的向量库类型"""
        return {
            name: store_cls.__name__
            for name, store_cls in cls._registry.items()
        }

    @classmethod
    def is_registered(cls, store_type: str) -> bool:
        """检查向量库类型是否已注册"""
        return store_type.lower() in cls._registry


class MetadataStoreFactory:
    """
    元数据存储工厂

    内置注册 sqlalchemy 适配器（支持 SQLite / PostgreSQL / MySQL），
    支持运行时通过 register() 扩展其他后端（如 Redis）。

    使用示例:
        store = MetadataStoreFactory.create("sqlalchemy")
        store = MetadataStoreFactory.create("sqlalchemy", db=custom_db)

    扩展方式:
        MetadataStoreFactory.register("redis", RedisMetadataStore)
    """

    # 注册表：{store_type: StoreClass}
    _registry: Dict[str, Type[BaseMetadataStore]] = {}

    @classmethod
    def _init_default_registry(cls) -> None:
        """初始化默认注册表（惰性导入避免循环依赖）"""
        if "sqlalchemy" in cls._registry:
            return
        from func.kb_system_langchain.metadata_store import SqlAlchemyMetadataStore
        cls.register("sqlalchemy", SqlAlchemyMetadataStore)

    @classmethod
    def register(cls, store_type: str, store_cls: Type[BaseMetadataStore]) -> None:
        """
        注册新的元数据存储类型

        Args:
            store_type: 类型名称（如 "redis", "mongodb"）
            store_cls:  实现了 BaseMetadataStore 的类

        示例:
            MetadataStoreFactory.register("redis", RedisMetadataStore)
        """
        if not issubclass(store_cls, BaseMetadataStore):
            raise TypeError(f"{store_cls.__name__} 必须继承 BaseMetadataStore")
        cls._registry[store_type.lower()] = store_cls
        print(f"[MetadataStoreFactory] 注册元数据存储类型: {store_type} -> {store_cls.__name__}")

    @classmethod
    def create(cls, store_type: str = "sqlalchemy", **kwargs) -> BaseMetadataStore:
        """
        创建元数据存储实例

        Args:
            store_type: 存储类型 (sqlalchemy / ...)
            **kwargs:   传递给构造函数的参数（如 db=...）

        Returns:
            BaseMetadataStore: 元数据存储实例
        """
        cls._init_default_registry()
        store_type = store_type.lower()

        if store_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的元数据存储类型: '{store_type}'。可用类型: {available}"
            )

        store_cls = cls._registry[store_type]

        try:
            instance = store_cls(**kwargs)
            print(f"[MetadataStoreFactory] 创建 {store_cls.__name__} 成功")
            return instance
        except Exception as e:
            raise RuntimeError(
                f"创建元数据存储实例失败 [{store_type}]: {e}"
            ) from e

    @classmethod
    def list_registered(cls) -> Dict[str, str]:
        """列出所有已注册的元数据存储类型"""
        cls._init_default_registry()
        return {
            name: store_cls.__name__
            for name, store_cls in cls._registry.items()
        }

    @classmethod
    def is_registered(cls, store_type: str) -> bool:
        """检查元数据存储类型是否已注册"""
        cls._init_default_registry()
        return store_type.lower() in cls._registry


class KBManagerFactory:
    """
    知识库管理器工厂

    根据配置创建对应的知识库管理器实例，支持运行时注册扩展。

    内置注册: default -> KnowledgeBaseManager（惰性加载，避免循环依赖）

    使用示例:
        # 零配置，自动从环境变量读取
        manager = KBManagerFactory.create("default")

        # 注入自定义配置
        manager = KBManagerFactory.create(
            "default",
            vectordb_config=my_vdb_config,
            embedding_config=my_emb_config,
            metadata_store=custom_metadata_store,
        )

    扩展方式:
        KBManagerFactory.register("pgvector", PGVectorKBManager)
    """

    # 注册表：{manager_type: ManagerClass}
    _registry: Dict[str, Type[BaseKnowledgeBaseManager]] = {}

    @classmethod
    def _init_default_registry(cls) -> None:
        """初始化默认注册表（使用惰性导入避免循环依赖）"""
        if "default" in cls._registry:
            return
        from func.kb_system_langchain.kb_manager import KnowledgeBaseManager
        cls.register("default", KnowledgeBaseManager)

    @classmethod
    def register(cls, manager_type: str, manager_cls: Type[BaseKnowledgeBaseManager]) -> None:
        """
        注册新的知识库管理器类型

        Args:
            manager_type: 类型名称（如 "pgvector", "weaviate"）
            manager_cls:  实现了 BaseKnowledgeBaseManager 的类

        示例:
            KBManagerFactory.register("pgvector", PGVectorKBManager)
        """
        if not issubclass(manager_cls, BaseKnowledgeBaseManager):
            raise TypeError(f"{manager_cls.__name__} 必须继承 BaseKnowledgeBaseManager")
        cls._registry[manager_type.lower()] = manager_cls
        # print(f"[KBManagerFactory] 注册知识库管理器类型: {manager_type} -> {manager_cls.__name__}")

    @classmethod
    def create(
        cls,
        manager_type: str = "default",
        **kwargs,
    ) -> BaseKnowledgeBaseManager:
        """
        创建知识库管理器实例

        Args:
            manager_type: 管理器类型 (default / ...)
            **kwargs:     传递给管理器构造函数的关键字参数
                         支持: vectordb_config, embedding_config, metadata_store, db, document_loader

        Returns:
            BaseKnowledgeBaseManager: 知识库管理器实例

        Raises:
            ValueError: 不支持的管理器类型
        """
        cls._init_default_registry()

        manager_type = manager_type.lower()

        if manager_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的知识库管理器类型: '{manager_type}'。可用类型: {available}"
            )

        manager_cls = cls._registry[manager_type]

        try:
            accepted = {"vectordb_config", "embedding_config", "metadata_store", "db", "document_loader"}
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted}
            instance = manager_cls(**filtered_kwargs)
            # print(f"[KBManagerFactory] 创建 {manager_cls.__name__} 成功")
            return instance
        except Exception as e:
            raise RuntimeError(
                f"创建知识库管理器实例失败 [{manager_type}]: {e}"
            ) from e

    @classmethod
    def list_registered(cls) -> Dict[str, str]:
        """列出所有已注册的知识库管理器类型"""
        cls._init_default_registry()
        return {
            name: manager_cls.__name__
            for name, manager_cls in cls._registry.items()
        }

    @classmethod
    def is_registered(cls, manager_type: str) -> bool:
        """检查知识库管理器类型是否已注册"""
        cls._init_default_registry()
        return manager_type.lower() in cls._registry
