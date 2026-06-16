"""
元数据存储适配器包

提供知识库元数据的持久化能力，支持多种后端：
- SqlAlchemyMetadataStore: 基于 SQLAlchemy，支持 SQLite / PostgreSQL / MySQL
"""

from func.kb_system_langchain.metadata_store.sqlalchemy_store import (
    SqlAlchemyMetadataStore,
    get_metadata_store,
)

__all__ = [
    "SqlAlchemyMetadataStore",
    "get_metadata_store",
]
