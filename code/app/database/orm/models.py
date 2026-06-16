"""
SQLAlchemy ORM 模型定义

三张核心表：
- kb_metadata: 知识库元数据
- documents:   文档元数据
- doc_kb_map:   文档-知识库多对多映射
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.orm.session import Base


def _iso(v: Any) -> str:
    """将 datetime 转为 ISO 字符串，确保与旧代码兼容"""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


class KBMetadata(Base):
    """知识库元数据表"""
    __tablename__ = "kb_metadata"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(Text, default="")
    num_docs = Column(Integer, default=0)
    num_docs_enable = Column(Integer, default=0)
    bool_enable = Column(Integer, default=1)
    bool_delete = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    create_by = Column(String(64), default="")
    update_by = Column(String(64), default="")
    label = Column(String(64), default="inquiry")

    # 关联映射记录
    doc_maps = relationship("DocKBMap", back_populates="kb", lazy="select")

    __table_args__ = (
        Index("idx_kb_bool_delete", "bool_delete"),
        Index("idx_kb_label", "label"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "num_docs": self.num_docs or 0,
            "num_docs_enable": self.num_docs_enable or 0,
            "bool_enable": self.bool_enable,
            "bool_delete": self.bool_delete,
            "create_time": _iso(self.create_time),
            "update_time": _iso(self.update_time),
            "create_by": self.create_by or "",
            "update_by": self.update_by or "",
            "label": self.label or "inquiry",
        }


class Documents(Base):
    """文档元数据表"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    title = Column(String(64), default="")
    type = Column(String(64), default="")
    create_time = Column(DateTime, default=datetime.now)
    create_by = Column(String(64), default="")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    update_by = Column(String(64), default="")
    effective_time = Column(DateTime, default=None)
    expiration_time = Column(DateTime, default=None)
    vector_status = Column(String(64), default="processing")
    bool_enable = Column(Integer, default=1)
    bool_delete = Column(Integer, default=0)

    # 关联映射记录
    kb_maps = relationship("DocKBMap", back_populates="doc", lazy="select")

    __table_args__ = (
        Index("idx_doc_bool_delete", "bool_delete"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title or "",
            "type": self.type or "",
            "create_time": _iso(self.create_time),
            "create_by": self.create_by or "",
            "update_time": _iso(self.update_time),
            "update_by": self.update_by or "",
            "effective_time": _iso(self.effective_time) if self.effective_time else None,
            "expiration_time": _iso(self.expiration_time) if self.expiration_time else None,
            "vector_status": self.vector_status or "processing",
            "bool_enable": self.bool_enable,
            "bool_delete": self.bool_delete,
        }


class DocKBMap(Base):
    """文档-知识库多对多映射表"""
    __tablename__ = "doc_kb_map"

    id = Column(String(36), primary_key=True)
    kb_id = Column(String(36), ForeignKey("kb_metadata.id", ondelete="CASCADE"), nullable=False)
    doc_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    kb = relationship("KBMetadata", back_populates="doc_maps")
    doc = relationship("Documents", back_populates="kb_maps")

    __table_args__ = (
        UniqueConstraint("kb_id", "doc_id", name="uq_kb_doc"),
        Index("idx_doc_kb_map_kb_id", "kb_id"),
        Index("idx_doc_kb_map_doc_id", "doc_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kb_id": self.kb_id,
            "doc_id": self.doc_id,
        }
