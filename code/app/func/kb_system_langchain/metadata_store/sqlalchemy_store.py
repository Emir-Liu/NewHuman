"""
SQLAlchemy 元数据存储适配器

封装 KnowledgeBaseDB，实现 BaseMetadataStore 接口。
通过 SQLAlchemy 支持 SQLite / PostgreSQL / MySQL 三种关系数据库，
数据库类型由 DATABASE_TYPE 环境变量控制。
"""

from typing import Dict, Any, Optional

from database.knowledge_base_db import KnowledgeBaseDB, get_db
from func.kb_system_langchain.interfaces import BaseMetadataStore


class SqlAlchemyMetadataStore(BaseMetadataStore):
    """
    基于 SQLAlchemy 的元数据存储实现

    内部委托给 KnowledgeBaseDB，后者已通过 SQLAlchemy 支持多数据库切换。
    """

    def __init__(self, db: Optional[KnowledgeBaseDB] = None):
        self._db = db or get_db()

    # ---- 知识库 ----

    def create_knowledge_base(
        self, name: str, description: str = "", label: str = "inquiry",
        bool_activate: int = 1, created_by: str = "system",
    ) -> Dict[str, Any]:
        return self._db.create_knowledge_base(
            name=name, description=description, label=label,
            bool_activate=bool_activate, created_by=created_by,
        )

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get_knowledge_base(kb_id)

    def list_knowledge_bases(
        self, page: int = 1, limit: int = 20,
        label: Optional[str] = None, exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        return self._db.list_knowledge_bases(
            page=page, limit=limit, label=label, exclude_deleted=exclude_deleted,
        )

    def update_knowledge_base(
        self, kb_id: str, name: Optional[str] = None,
        description: Optional[str] = None, updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        return self._db.update_knowledge_base(
            kb_id=kb_id, name=name, description=description, updated_by=updated_by,
        )

    def soft_delete_knowledge_base(self, kb_id: str) -> bool:
        return self._db.soft_delete_knowledge_base(kb_id)

    def count_knowledge_bases(self, label: Optional[str] = None) -> int:
        return self._db.count_knowledge_bases(label=label)

    def update_kb_doc_counts(self, kb_id: str) -> None:
        self._db.update_kb_doc_counts(kb_id)

    # ---- 文档 ----

    def create_document(
        self, kb_id: str, name: str, title: str = "",
        doc_type: str = "", effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None, created_by: str = "system",
    ) -> Dict[str, Any]:
        return self._db.create_document(
            kb_id=kb_id, name=name, title=title, doc_type=doc_type,
            effective_time=effective_time, expiration_time=expiration_time,
            created_by=created_by,
        )

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get_document(doc_id)

    def list_documents(
        self, kb_id: str, page: int = 1, limit: int = 20,
        exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        return self._db.list_documents(
            kb_id=kb_id, page=page, limit=limit, exclude_deleted=exclude_deleted,
        )

    def update_document(
        self, doc_id: str, name: Optional[str] = None,
        title: Optional[str] = None, effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None, vector_status: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        return self._db.update_document(
            doc_id=doc_id, name=name, title=title,
            effective_time=effective_time, expiration_time=expiration_time,
            vector_status=vector_status, updated_by=updated_by,
        )

    def soft_delete_document(self, doc_id: str, kb_id: str) -> bool:
        return self._db.soft_delete_document(doc_id=doc_id, kb_id=kb_id)

    def toggle_document(
        self, doc_id: str, enable: bool, kb_id: str,
    ) -> Optional[Dict[str, Any]]:
        return self._db.toggle_document(doc_id=doc_id, enable=enable, kb_id=kb_id)

    def get_kb_for_document(self, doc_id: str) -> Optional[str]:
        return self._db.get_kb_for_document(doc_id)


# 全局元数据存储单例
_metadata_store: Optional[SqlAlchemyMetadataStore] = None


def get_metadata_store(db: Optional[KnowledgeBaseDB] = None) -> SqlAlchemyMetadataStore:
    """获取全局元数据存储实例"""
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = SqlAlchemyMetadataStore(db=db)
    return _metadata_store
