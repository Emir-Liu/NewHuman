"""
向量知识库基础类和数据模型
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Document:
    """文档数据结构"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: Optional[str] = None


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float


@dataclass
class KnowledgeBaseInfo:
    """知识库元数据信息"""
    kb_id: str                          # 知识库唯一ID
    name: str                           # 知识库名称
    description: str                    # 知识库描述
    created_at: str                     # 创建时间 (ISO格式)
    updated_at: str                     # 更新时间
    doc_count: int = 0                  # 文档数量
    status: str = "active"              # 状态: active/inactive


class BaseVectorStore(ABC):
    """向量库基类"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """搜索文档"""
        pass
    
    @abstractmethod
    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空知识库"""
        pass
    
    @property
    @abstractmethod
    def doc_count(self) -> int:
        """文档数量"""
        pass
