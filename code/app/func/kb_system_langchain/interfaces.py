"""
知识库系统抽象接口

定义向量库（BaseVectorStore）、元数据存储（BaseMetadataStore）
和知识库管理器（BaseKnowledgeBaseManager）的抽象基类，
所有具体实现必须实现这些接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from func.kb_system_langchain.models import (
    Document, SearchResult, KnowledgeBaseInfo,
    DocumentInfo, ChunkInfo,
)


# ==================== 向量库基础接口 ====================

class BaseVectorStore(ABC):
    """向量库抽象基类"""

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库，返回文档ID列表"""
        pass

    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """从向量库删除文档"""
        pass

    @abstractmethod
    def update_document(self, doc_id: str, document: Document) -> bool:
        """更新向量库中的文档"""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, score_threshold: Optional[float] = None) -> List[SearchResult]:
        """向量相似度搜索"""
        pass

    @abstractmethod
    def list_documents(self) -> List[Document]:
        """列出向量库中所有文档"""
        pass

    @abstractmethod
    def get_by_ids(self, ids: List[str]) -> List[Document]:
        """按ID批量获取文档"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空向量库"""
        pass

    @property
    @abstractmethod
    def doc_count(self) -> int:
        """向量库中文档数量"""
        pass


# ==================== 元数据存储基础接口 ====================

class BaseMetadataStore(ABC):
    """元数据存储抽象接口

    管理知识库、文档的元数据 CRUD，与底层关系数据库解耦。
    支持 SQLAlchemy（SQLite/PostgreSQL/MySQL）等不同后端替换。
    """

    # ---- 知识库 ----

    @abstractmethod
    def create_knowledge_base(
        self, name: str, description: str = "", label: str = "inquiry",
        bool_activate: int = 1, created_by: str = "system",
    ) -> Dict[str, Any]:
        """创建知识库，返回数据库行字典"""
        pass

    @abstractmethod
    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取单个知识库"""
        pass

    @abstractmethod
    def list_knowledge_bases(
        self, page: int = 1, limit: int = 20,
        label: Optional[str] = None, exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        """分页列出知识库"""
        pass

    @abstractmethod
    def update_knowledge_base(
        self, kb_id: str, name: Optional[str] = None,
        description: Optional[str] = None, updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        """更新知识库信息"""
        pass

    @abstractmethod
    def soft_delete_knowledge_base(self, kb_id: str) -> bool:
        """软删除知识库"""
        pass

    @abstractmethod
    def count_knowledge_bases(self, label: Optional[str] = None) -> int:
        """统计知识库数量"""
        pass

    @abstractmethod
    def update_kb_doc_counts(self, kb_id: str) -> None:
        """更新知识库文档计数"""
        pass

    # ---- 文档 ----

    @abstractmethod
    def create_document(
        self, kb_id: str, name: str, title: str = "",
        doc_type: str = "", effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None, created_by: str = "system",
    ) -> Dict[str, Any]:
        """创建文档记录，返回数据库行字典"""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        pass

    @abstractmethod
    def list_documents(
        self, kb_id: str, page: int = 1, limit: int = 20,
        exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        """分页列出知识库下的文档"""
        pass

    @abstractmethod
    def update_document(
        self, doc_id: str, name: Optional[str] = None,
        title: Optional[str] = None, effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None, vector_status: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        """更新文档信息"""
        pass

    @abstractmethod
    def soft_delete_document(self, doc_id: str, kb_id: str) -> bool:
        """软删除文档"""
        pass

    @abstractmethod
    def toggle_document(
        self, doc_id: str, enable: bool, kb_id: str,
    ) -> Optional[Dict[str, Any]]:
        """启用/禁用文档"""
        pass

    @abstractmethod
    def get_kb_for_document(self, doc_id: str) -> Optional[str]:
        """获取文档所属知识库ID"""
        pass


# ==================== 知识库管理器基础接口 ====================

class BaseKnowledgeBaseManager(ABC):
    """知识库管理器抽象基类

    定义知识库、文档、切片的完整管理接口。
    具体实现（如 SqliteKBManager）通过继承本类来保证接口一致性，
    支持未来扩展不同的存储后端（如 pgvector、Weaviate 等）。
    """

    # ---- 知识库 CRUD ----

    @abstractmethod
    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        label: str = "inquiry",
        bool_activate: int = 1,
        created_by: str = "system",
    ) -> KnowledgeBaseInfo:
        """创建新知识库"""
        pass

    @abstractmethod
    def list_knowledge_bases(
        self,
        page: int = 1,
        limit: int = 20,
        label: Optional[str] = None,
    ) -> Dict:
        """分页列出知识库"""
        pass

    @abstractmethod
    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBaseInfo]:
        """获取单个知识库信息"""
        pass

    @abstractmethod
    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[KnowledgeBaseInfo]:
        """更新知识库信息"""
        pass

    @abstractmethod
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """软删除知识库"""
        pass

    # ---- 文档 CRUD ----

    @abstractmethod
    def upload_document(
        self,
        kb_id: str,
        file_path: str,
        file_name: str,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        created_by: str = "system",
    ) -> DocumentInfo:
        """上传文档到知识库（加载、分块、向量化）"""
        pass

    @abstractmethod
    def create_document(
        self,
        kb_id: str,
        name: str,
        title: str = "",
        doc_type: str = "",
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        created_by: str = "system",
    ) -> DocumentInfo:
        """创建空文档记录（不写入向量库）"""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """获取单个文档信息"""
        pass

    @abstractmethod
    def list_documents(
        self,
        kb_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict:
        """分页列出知识库下的文档"""
        pass

    @abstractmethod
    def update_document(
        self,
        doc_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[DocumentInfo]:
        """更新文档信息"""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """软删除文档"""
        pass

    @abstractmethod
    def toggle_document(self, doc_id: str, enable: bool) -> Optional[DocumentInfo]:
        """启用/禁用文档"""
        pass

    # ---- 切片/知识管理 ----

    @abstractmethod
    def create_chunks(
        self,
        doc_id: str,
        segments: List[dict],
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
    ) -> List[ChunkInfo]:
        """为文档创建切片"""
        pass

    @abstractmethod
    def get_chunk(self, chunk_id: str, doc_id: str) -> Optional[ChunkInfo]:
        """获取单个切片信息"""
        pass

    @abstractmethod
    def list_chunks(
        self,
        doc_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict:
        """分页列出文档下的切片"""
        pass

    @abstractmethod
    def update_chunk(
        self,
        chunk_id: str,
        doc_id: str,
        content: Optional[str] = None,
        enabled: Optional[bool] = None,
        chunk_metadata: Optional[List[dict]] = None,
    ) -> Optional[ChunkInfo]:
        """更新切片内容"""
        pass

    @abstractmethod
    def delete_chunk(self, chunk_id: str, doc_id: str) -> bool:
        """软删除切片"""
        pass

    # ---- 向量检索 ----

    @abstractmethod
    def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict:
        """在指定知识库中检索"""
        pass

    @abstractmethod
    def search_by_label(
        self,
        query: str,
        label: str = "inquiry",
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict:
        """按标签在多个知识库中检索"""
        pass
