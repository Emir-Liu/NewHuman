"""
知识库关系数据库层（ORM 版）

使用 SQLAlchemy ORM 管理知识库、文档、文档-知识库映射的元数据持久化。
支持 SQLite / PostgreSQL / MySQL 三种数据库，通过环境变量切换。
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.orm.models import KBMetadata, Documents, DocKBMap
from database.orm.session import init_db, get_session


class KnowledgeBaseDB:
    """
    知识库 ORM 操作类（线程安全，基于 scoped_session）

    存储以下对象：
    - kb_metadata: 知识库元数据
    - documents: 文档元数据
    - doc_kb_map: 文档-知识库映射关系
    """

    def __init__(self):
        """初始化：自动建表（首次调用）"""
        init_db()

    # ==================== 知识库 CRUD ====================

    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        label: str = "inquiry",
        bool_activate: int = 1,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """创建知识库"""
        kb_id = str(uuid.uuid4())
        now = datetime.now()

        session: Session = get_session()
        try:
            kb = KBMetadata(
                id=kb_id,
                name=name,
                description=description,
                bool_enable=bool_activate,
                label=label,
                create_by=created_by,
                update_by=created_by,
                create_time=now,
                update_time=now,
            )
            session.add(kb)
            session.commit()
            return kb.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取单个知识库（包含已删除的）"""
        session: Session = get_session()
        try:
            kb = session.query(KBMetadata).filter(KBMetadata.id == kb_id).first()
            return kb.to_dict() if kb else None
        finally:
            session.close()

    def list_knowledge_bases(
        self,
        page: int = 1,
        limit: int = 20,
        label: Optional[str] = None,
        exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        """分页列出知识库"""
        session: Session = get_session()
        try:
            q = session.query(KBMetadata)

            if exclude_deleted:
                q = q.filter(KBMetadata.bool_delete == 0)
            if label:
                q = q.filter(KBMetadata.label == label)

            total = q.count()
            offset = (page - 1) * limit
            rows = q.order_by(KBMetadata.create_time.desc()).offset(offset).limit(limit).all()

            return {
                "items": [r.to_dict() for r in rows],
                "total": total,
                "page": page,
                "page_size": limit,
            }
        finally:
            session.close()

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        """更新知识库信息"""
        session: Session = get_session()
        try:
            kb = session.query(KBMetadata).filter(KBMetadata.id == kb_id).first()
            if kb is None:
                return None

            if name is not None:
                kb.name = name
            if description is not None:
                kb.description = description

            kb.update_time = datetime.now()
            kb.update_by = updated_by
            session.commit()

            # refresh 后 to_dict 获取最新数据
            session.refresh(kb)
            return kb.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def soft_delete_knowledge_base(self, kb_id: str) -> bool:
        """软删除知识库"""
        session: Session = get_session()
        try:
            kb = session.query(KBMetadata).filter(
                KBMetadata.id == kb_id,
                KBMetadata.bool_delete == 0,
            ).first()
            if kb is None:
                return False

            kb.bool_delete = 1
            kb.update_time = datetime.now()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def toggle_knowledge_base(self, kb_id: str, enable: bool) -> Optional[Dict[str, Any]]:
        """启用/禁用知识库"""
        session: Session = get_session()
        try:
            kb = session.query(KBMetadata).filter(
                KBMetadata.id == kb_id,
                KBMetadata.bool_delete == 0,
            ).first()
            if kb is None:
                return None

            kb.bool_enable = 1 if enable else 0
            kb.update_time = datetime.now()
            session.commit()
            session.refresh(kb)
            return kb.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_kb_doc_counts(self, kb_id: str, session: Optional[Session] = None):
        """
        更新知识库文档计数。

        统计该知识库下未软删除的文档总数 + 启用数，
        并写回 kb_metadata 表的 num_docs / num_docs_enable 字段。

        Args:
            kb_id: 知识库ID
            session: 可选的已有 session，传入时不会自动关闭
        """
        _close = session is None
        if session is None:
            session = get_session()
        try:
            # 总数（不含软删除）
            total = session.query(func.count(DocKBMap.id)).join(
                Documents, DocKBMap.doc_id == Documents.id
            ).filter(
                DocKBMap.kb_id == kb_id,
                Documents.bool_delete == 0,
            ).scalar() or 0

            # 启用数
            enabled = session.query(func.count(DocKBMap.id)).join(
                Documents, DocKBMap.doc_id == Documents.id
            ).filter(
                DocKBMap.kb_id == kb_id,
                Documents.bool_delete == 0,
                Documents.bool_enable == 1,
            ).scalar() or 0

            kb = session.query(KBMetadata).filter(KBMetadata.id == kb_id).first()
            if kb:
                kb.num_docs = total
                kb.num_docs_enable = enabled
                kb.update_time = datetime.now()
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            if _close:
                session.close()

    # ==================== 文档 CRUD ====================

    def create_document(
        self,
        kb_id: str,
        name: str,
        title: str = "",
        doc_type: str = "",
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """创建文档并在知识库中注册"""
        doc_id = str(uuid.uuid4())
        map_id = str(uuid.uuid4())
        now = datetime.now()

        # 将 ISO 字符串转为 datetime（如果有）
        eff_time = datetime.fromisoformat(effective_time) if effective_time else None
        exp_time = datetime.fromisoformat(expiration_time) if expiration_time else None

        session: Session = get_session()
        try:
            doc = Documents(
                id=doc_id,
                name=name,
                title=title,
                type=doc_type,
                create_by=created_by,
                update_by=created_by,
                create_time=now,
                update_time=now,
                effective_time=eff_time,
                expiration_time=exp_time,
                vector_status="processing",
            )
            session.add(doc)

            # 建立映射
            mapping = DocKBMap(id=map_id, kb_id=kb_id, doc_id=doc_id)
            session.add(mapping)

            session.commit()

            # 更新知识库文档计数（复用当前 session）
            self.update_kb_doc_counts(kb_id, session=session)

            return doc.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        session: Session = get_session()
        try:
            doc = session.query(Documents).filter(Documents.id == doc_id).first()
            return doc.to_dict() if doc else None
        finally:
            session.close()

    def list_documents(
        self,
        kb_id: str,
        page: int = 1,
        limit: int = 20,
        exclude_deleted: bool = True,
    ) -> Dict[str, Any]:
        """分页列出知识库下的文档"""
        session: Session = get_session()
        try:
            q = session.query(Documents).join(
                DocKBMap, DocKBMap.doc_id == Documents.id
            ).filter(DocKBMap.kb_id == kb_id)

            if exclude_deleted:
                q = q.filter(Documents.bool_delete == 0)

            total = q.count()
            offset = (page - 1) * limit

            # 使用 ROW_NUMBER() 窗口函数计算 position（跨库兼容）
            position_expr = func.row_number().over(
                order_by=Documents.create_time.desc()
            ).label("position")

            rows = (
                session.query(Documents, position_expr)
                .join(DocKBMap, DocKBMap.doc_id == Documents.id)
                .filter(DocKBMap.kb_id == kb_id)
                .filter(Documents.bool_delete == 0 if exclude_deleted else True)
                .order_by(Documents.create_time.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            data = []
            for doc, pos in rows:
                d = doc.to_dict()
                d["position"] = pos
                data.append(d)

            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "has_more": offset + limit < total,
            }
        finally:
            session.close()

    def update_document(
        self,
        doc_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        vector_status: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        """更新文档信息"""
        session: Session = get_session()
        try:
            doc = session.query(Documents).filter(Documents.id == doc_id).first()
            if doc is None:
                return None

            if name is not None:
                doc.name = name
            if title is not None:
                doc.title = title
            if effective_time is not None:
                doc.effective_time = datetime.fromisoformat(effective_time) if effective_time else None
            if expiration_time is not None:
                doc.expiration_time = datetime.fromisoformat(expiration_time) if expiration_time else None
            if vector_status is not None:
                doc.vector_status = vector_status

            doc.update_time = datetime.now()
            doc.update_by = updated_by
            session.commit()
            session.refresh(doc)
            return doc.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def soft_delete_document(self, doc_id: str, kb_id: str) -> bool:
        """软删除文档"""
        session: Session = get_session()
        try:
            doc = session.query(Documents).filter(
                Documents.id == doc_id,
                Documents.bool_delete == 0,
            ).first()
            if doc is None:
                return False

            doc.bool_delete = 1
            doc.update_time = datetime.now()
            session.commit()

            # 更新知识库文档计数（复用当前 session）
            self.update_kb_doc_counts(kb_id, session=session)
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def toggle_document(self, doc_id: str, enable: bool, kb_id: str) -> Optional[Dict[str, Any]]:
        """启用/禁用文档"""
        session: Session = get_session()
        try:
            doc = session.query(Documents).filter(
                Documents.id == doc_id,
                Documents.bool_delete == 0,
            ).first()
            if doc is None:
                return None

            doc.bool_enable = 1 if enable else 0
            doc.update_time = datetime.now()
            session.commit()

            self.update_kb_doc_counts(kb_id, session=session)
            session.refresh(doc)
            return doc.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_kb_for_document(self, doc_id: str) -> Optional[str]:
        """获取文档所属知识库ID"""
        session: Session = get_session()
        try:
            mapping = session.query(DocKBMap).filter(
                DocKBMap.doc_id == doc_id
            ).first()
            return mapping.kb_id if mapping else None
        finally:
            session.close()

    def count_knowledge_bases(self, label: Optional[str] = None) -> int:
        """统计知识库数量"""
        session: Session = get_session()
        try:
            q = session.query(func.count(KBMetadata.id)).filter(
                KBMetadata.bool_delete == 0
            )
            if label:
                q = q.filter(KBMetadata.label == label)
            return q.scalar() or 0
        finally:
            session.close()


# 全局数据库实例（单例）
_db_instance: Optional[KnowledgeBaseDB] = None


def get_db() -> KnowledgeBaseDB:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = KnowledgeBaseDB()
    return _db_instance
