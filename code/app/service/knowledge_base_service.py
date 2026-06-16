"""
知识库服务层
处理知识库、文档、切片的核心业务逻辑
"""

import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from func.kb_system_langchain.kb_manager import get_kb_manager, KnowledgeBaseManager
from func.kb_system_langchain.models import KnowledgeBaseInfo, DocumentInfo, ChunkInfo
from schema.knowledge_base_model import (
    KnowledgeBaseItem, DocumentItem, ChunkItem,
    DocMetadataItem, ChunkMetadataItem,
)


class KnowledgeBaseService:
    """知识库服务"""

    def __init__(self):
        self._manager: Optional[KnowledgeBaseManager] = None

    @property
    def manager(self) -> KnowledgeBaseManager:
        if self._manager is None:
            self._manager = get_kb_manager()
        return self._manager

    # ==================== 知识库管理 ====================

    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        label: str = "inquiry",
        bool_activate: int = 1,
    ) -> Dict[str, Any]:
        """创建知识库"""
        kb_info = self.manager.create_knowledge_base(
            name=name,
            description=description,
            label=label,
            bool_activate=bool_activate,
        )
        return self._kb_info_to_dict(kb_info)

    def list_knowledge_bases(
        self,
        page: int = 1,
        limit: int = 20,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """列出知识库"""
        result = self.manager.list_knowledge_bases(page=page, limit=limit, label=label)
        items = [
            self._kb_info_to_dict(KnowledgeBaseInfo(**item))
            for item in result.get("items", [])
        ]
        return {
            "items": items,
            "total": result.get("total", 0),
            "page": result.get("page", page),
            "page_size": result.get("page_size", limit),
        }

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取单个知识库"""
        kb_info = self.manager.get_knowledge_base(kb_id)
        return self._kb_info_to_dict(kb_info) if kb_info else None

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新知识库"""
        kb_info = self.manager.update_knowledge_base(
            kb_id=kb_id,
            name=name,
            description=description,
        )
        return self._kb_info_to_dict(kb_info) if kb_info else None

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        return self.manager.delete_knowledge_base(kb_id)

    # ==================== 文档管理 ====================

    def upload_document(
        self,
        kb_id: str,
        file_content: bytes,
        file_name: str,
        effective_time: str = "",
        expiration_time: str = "",
        parse_mode: str = "",
        chunk_mode: str = "",
        q_column: str = "",
        a_column: str = "",
    ) -> Dict[str, Any]:
        """上传文档"""
        suffix = os.path.splitext(file_name)[1] or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            doc_info = self.manager.upload_document(
                kb_id=kb_id,
                file_path=tmp_path,
                file_name=file_name,
                effective_time=effective_time or None,
                expiration_time=expiration_time or None,
                parse_mode=parse_mode or None,
                chunk_mode=chunk_mode or None,
                q_column=q_column or None,
                a_column=a_column or None,
            )
            return self._doc_info_to_dict(doc_info)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def create_document(
        self,
        kb_id: str,
        name: str,
        title: str = "",
        doc_type: str = "",
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建文档记录"""
        doc_info = self.manager.create_document(
            kb_id=kb_id,
            name=name,
            title=title,
            doc_type=doc_type,
            effective_time=effective_time,
            expiration_time=expiration_time,
        )
        return self._doc_info_to_dict(doc_info)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档"""
        doc_info = self.manager.get_document(doc_id)
        return self._doc_info_to_dict(doc_info) if doc_info else None

    def list_documents(
        self,
        kb_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """列出文档"""
        result = self.manager.list_documents(kb_id=kb_id, page=page, limit=limit)
        data = [
            self._doc_info_to_dict(DocumentInfo(**item))
            for item in result.get("data", [])
        ]
        return {
            "data": data,
            "total": result.get("total", 0),
            "page": result.get("page", page),
            "limit": result.get("limit", limit),
            "has_more": result.get("has_more", False),
        }

    def update_document(
        self,
        doc_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新文档"""
        doc_info = self.manager.update_document(
            doc_id=doc_id,
            name=name,
            title=title,
            effective_time=effective_time,
            expiration_time=expiration_time,
        )
        return self._doc_info_to_dict(doc_info) if doc_info else None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        return self.manager.delete_document(doc_id)

    def toggle_document(self, doc_id: str, enable: bool) -> Optional[Dict[str, Any]]:
        """启用/禁用文档"""
        doc_info = self.manager.toggle_document(doc_id, enable)
        return self._doc_info_to_dict(doc_info) if doc_info else None

    def re_vectorize_document(self, doc_id: str) -> bool:
        """重新向量化文档"""
        # TODO: 实现重新向量化逻辑
        doc_info = self.manager.get_document(doc_id)
        if doc_info is None:
            return False
        # 标记为 processing（通过 metadata_store，不直接访问数据库）
        self.manager.metadata_store.update_document(doc_id, vector_status="processing")
        return True

    # ==================== 切片管理 ====================

    def create_chunks(
        self,
        doc_id: str,
        segments: List[dict],
    ) -> Dict[str, Any]:
        """创建切片"""
        chunk_infos = self.manager.create_chunks(
            doc_id=doc_id,
            segments=segments,
        )
        return {
            "data": [self._chunk_info_to_dict(c) for c in chunk_infos],
        }

    def get_chunk(self, chunk_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取切片"""
        chunk_info = self.manager.get_chunk(chunk_id, doc_id)
        return self._chunk_info_to_dict(chunk_info) if chunk_info else None

    def list_chunks(
        self,
        doc_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """列出切片"""
        return self.manager.list_chunks(doc_id=doc_id, page=page, limit=limit)

    def update_chunk(
        self,
        chunk_id: str,
        doc_id: str,
        content: Optional[str] = None,
        enabled: Optional[bool] = None,
        chunk_metadata: Optional[List[dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新切片"""
        chunk_info = self.manager.update_chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            content=content,
            enabled=enabled,
            chunk_metadata=chunk_metadata,
        )
        return self._chunk_info_to_dict(chunk_info) if chunk_info else None

    def delete_chunk(self, chunk_id: str, doc_id: str) -> bool:
        """删除切片"""
        return self.manager.delete_chunk(chunk_id, doc_id)

    # ==================== 检索 ====================

    def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict[str, Any]:
        """检索知识库"""
        return self.manager.search(
            kb_id=kb_id,
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            score_threshold_enabled=score_threshold_enabled,
        )

    def search_by_label(
        self,
        query: str,
        label: str = "inquiry",
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict[str, Any]:
        """按标签联合检索"""
        return self.manager.search_by_label(
            query=query,
            label=label,
            top_k=top_k,
            score_threshold=score_threshold,
            score_threshold_enabled=score_threshold_enabled,
        )

    # ==================== 数据转换 ====================

    @staticmethod
    def _kb_info_to_dict(kb_info: KnowledgeBaseInfo) -> Dict[str, Any]:
        """KnowledgeBaseInfo 转为 API 字典"""
        return {
            "id": kb_info.id,
            "name": kb_info.name,
            "description": kb_info.description,
            "bool_activate": kb_info.bool_enable,
            "num_docs": kb_info.num_docs,
            "num_docs_enable": kb_info.num_docs_enable,
            "created_by": kb_info.create_by,
            "created_at": kb_info.create_time,
            "updated_by": kb_info.update_by,
            "updated_at": kb_info.update_time,
            "label": kb_info.label,
        }

    @staticmethod
    def _doc_info_to_dict(doc_info: DocumentInfo) -> Dict[str, Any]:
        """DocumentInfo 转为 API 字典"""
        return {
            "id": doc_info.id,
            "position": doc_info.position,
            "name": doc_info.name,
            "extension": doc_info.type,
            "created_by": doc_info.create_by,
            "created_at": doc_info.create_time,
            "updated_by": doc_info.update_by,
            "updated_at": doc_info.update_time,
            "indexing_status": doc_info.vector_status,
            "error": "",
            "enabled": doc_info.enabled,
            "archived": False,
            "doc_metadata": doc_info.doc_metadata,
        }

    @staticmethod
    def _chunk_info_to_dict(chunk_info: ChunkInfo) -> Dict[str, Any]:
        """ChunkInfo 转为 API 字典"""
        return {
            "id": chunk_info.id,
            "position": chunk_info.index,
            "document_id": chunk_info.doc_id,
            "content": chunk_info.content,
            "enabled": chunk_info.enabled,
            "indexing_status": "success",
            "created_by": "",
            "created_at": chunk_info.create_time,
            "updated_by": "",
            "updated_at": chunk_info.create_time,
            "error": "",
            "chunk_metadata": chunk_info.chunk_metadata,
        }


# 全局服务实例
knowledge_base_service = KnowledgeBaseService()
