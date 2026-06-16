"""
知识库管理器

整合元数据存储（BaseMetadataStore） + 向量库（Chroma/Milvus），
提供知识库、文档、切片的完整 CRUD 和软删除支持。
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from database.knowledge_base_db import KnowledgeBaseDB
from func.kb_system_langchain.models import (
    KnowledgeBaseInfo, DocumentInfo, ChunkInfo,
    Document, SearchResult,
)
from func.kb_system_langchain.interfaces import (
    BaseVectorStore, BaseKnowledgeBaseManager, BaseMetadataStore,
)
from func.kb_system_langchain.factories import VectorStoreFactory
from func.kb_system_langchain.metadata_store import (
    SqlAlchemyMetadataStore, get_metadata_store,
)
from func.kb_system_langchain.document_loader import (
    DocumentLoader, get_document_loader,
)


class KnowledgeBaseManager(BaseKnowledgeBaseManager):
    """
    多知识库管理器

    使用 BaseMetadataStore 管理元数据（支持 SQLite / PG / MySQL 切换），
    通过 VectorStoreFactory 创建向量库实例（支持 Chroma / Milvus 切换）。

    数据库类型由 DATABASE_TYPE 环境变量决定；
    向量库类型由 VECTOR_STORE_TYPE 环境变量决定。
    """

    # 最大知识库数量
    MAX_KB_COUNT = 50

    def __init__(
        self,
        vectordb_config: Optional[VectorDBConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
        metadata_store: Optional[BaseMetadataStore] = None,
        db: Optional[KnowledgeBaseDB] = None,  # 向后兼容：传入后自动包装为 SqlAlchemyMetadataStore
        document_loader: Optional[DocumentLoader] = None,
    ):
        self.vectordb_config = vectordb_config or VectorDBConfig()
        self.embedding_config = embedding_config or EmbeddingConfig()

        # 元数据存储：优先使用传入的 metadata_store，否则用 db 包装，最后 fallback 到全局单例
        if metadata_store is not None:
            self.metadata_store = metadata_store
        elif db is not None:
            self.metadata_store = SqlAlchemyMetadataStore(db=db)
        else:
            self.metadata_store = get_metadata_store()

        self.document_loader = document_loader or get_document_loader()

        self.base_path = Path(self.vectordb_config.persist_directory)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 知识库实例缓存（依赖 BaseVectorStore 抽象，不绑定具体实现）
        self._knowledge_bases: Dict[str, BaseVectorStore] = {}
        self._current_kb_id: Optional[str] = None

    # ==================== 内部辅助 ====================

    def _get_kb_path(self, kb_id: str) -> Path:
        """获取知识库向量存储路径"""
        return self.base_path / kb_id

    def _get_or_create_kb_instance(self, kb_id: str) -> BaseVectorStore:
        """获取或初始化知识库的向量存储实例（通过工厂创建）"""
        kb_exists = self.metadata_store.get_knowledge_base(kb_id)
        if kb_exists is None:
            raise ValueError(f"知识库不存在: {kb_id}")

        if kb_id in self._knowledge_bases:
            return self._knowledge_bases[kb_id]

        kb_path = self._get_kb_path(kb_id)
        kb_path.mkdir(parents=True, exist_ok=True)

        kb_config = VectorDBConfig()
        kb_config.persist_directory = str(kb_path)

        # 通过工厂创建向量库实例（根据 VECTOR_STORE_TYPE 环境变量）
        kb = VectorStoreFactory.create(
            store_type=kb_config.store_type,
            vectordb_config=kb_config,
            embedding_config=self.embedding_config,
        )
        self._knowledge_bases[kb_id] = kb
        return kb

    def _row_to_kb_info(self, row: dict) -> KnowledgeBaseInfo:
        """将数据库行转换为 KnowledgeBaseInfo"""
        return KnowledgeBaseInfo(
            id=row["id"],
            name=row["name"],
            description=row.get("description", ""),
            num_docs=row.get("num_docs", 0),
            num_docs_enable=row.get("num_docs_enable", 0),
            bool_enable=row.get("bool_enable", 1),
            bool_delete=row.get("bool_delete", 0),
            create_time=row.get("create_time", ""),
            update_time=row.get("update_time", ""),
            create_by=row.get("create_by", ""),
            update_by=row.get("update_by", ""),
            label=row.get("label", "inquiry"),
        )

    def _row_to_doc_info(self, row: dict) -> DocumentInfo:
        """将数据库行转换为 DocumentInfo"""
        return DocumentInfo(
            id=row["id"],
            name=row["name"],
            title=row.get("title", ""),
            type=row.get("type", ""),
            create_time=row.get("create_time", ""),
            create_by=row.get("create_by", ""),
            update_time=row.get("update_time", ""),
            update_by=row.get("update_by", ""),
            effective_time=row.get("effective_time"),
            expiration_time=row.get("expiration_time"),
            vector_status=row.get("vector_status", "processing"),
            bool_enable=row.get("bool_enable", 1),
            bool_delete=row.get("bool_delete", 0),
            position=row.get("position", 0),
        )

    # ==================== 知识库管理 ====================

    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        label: str = "inquiry",
        bool_activate: int = 1,
        created_by: str = "system",
    ) -> KnowledgeBaseInfo:
        """
        创建新知识库

        Args:
            name: 知识库名称（5-64字符）
            description: 知识库描述（0-1024字符）
            label: 标签 (inquiry/business_des/business_data)
            bool_activate: 是否激活
            created_by: 创建人

        Returns:
            KnowledgeBaseInfo: 创建的知识库信息
        """
        # 校验
        if len(name) < 5 or len(name) > 64:
            raise ValueError("知识库名称长度需在5-64个字符之间")
        if len(description) > 1024:
            raise ValueError("知识库描述长度不能超过1024个字符")
        if label not in ("inquiry", "business_des", "business_data"):
            raise ValueError("label 必须为 inquiry / business_des / business_data")

        # 检查数量限制
        count = self.metadata_store.count_knowledge_bases()
        if count >= self.MAX_KB_COUNT:
            raise ValueError(f"知识库数量已达上限 {self.MAX_KB_COUNT} 个")

        row = self.metadata_store.create_knowledge_base(
            name=name,
            description=description,
            label=label,
            bool_activate=bool_activate,
            created_by=created_by,
        )

        # 创建向量存储目录
        kb_path = self._get_kb_path(row["id"])
        kb_path.mkdir(parents=True, exist_ok=True)

        return self._row_to_kb_info(row)

    def list_knowledge_bases(
        self,
        page: int = 1,
        limit: int = 20,
        label: Optional[str] = None,
    ) -> Dict:
        """分页列出知识库"""
        return self.metadata_store.list_knowledge_bases(page=page, limit=limit, label=label)

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBaseInfo]:
        """获取单个知识库信息"""
        row = self.metadata_store.get_knowledge_base(kb_id)
        return self._row_to_kb_info(row) if row else None

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[KnowledgeBaseInfo]:
        """更新知识库信息"""
        if name is not None and (len(name) < 5 or len(name) > 64):
            raise ValueError("知识库名称长度需在5-64个字符之间")
        if description is not None and len(description) > 1024:
            raise ValueError("知识库描述长度不能超过1024个字符")

        row = self.metadata_store.update_knowledge_base(kb_id, name, description, updated_by)
        return self._row_to_kb_info(row) if row else None

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """软删除知识库"""
        success = self.metadata_store.soft_delete_knowledge_base(kb_id)
        if not success:
            return False

        # 清理内存缓存
        if kb_id in self._knowledge_bases:
            del self._knowledge_bases[kb_id]
        if self._current_kb_id == kb_id:
            self._current_kb_id = None

        return True

    # ==================== 文档管理 ====================

    def upload_document(
        self,
        kb_id: str,
        file_path: str,
        file_name: str,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        parse_mode: Optional[str] = None,
        chunk_mode: Optional[str] = None,
        q_column: Optional[str] = None,
        a_column: Optional[str] = None,
        created_by: str = "system",
    ) -> DocumentInfo:
        """
        上传文档到知识库

        parse_mode: 解析方式（留空=auto，按后缀默认；table=表格行字典列表）
        chunk_mode: 切片方式（留空=auto；row=一行一切片；qa=Q向量化A入metadata）
        """
        kb_info = self.metadata_store.get_knowledge_base(kb_id)
        if kb_info is None:
            raise ValueError(f"知识库不存在: {kb_id}")

        normalized_chunk_mode = DocumentLoader.normalize_chunk_mode(chunk_mode)
        doc_type = DocumentLoader.resolve_doc_type(file_name, normalized_chunk_mode)

        row = self.metadata_store.create_document(
            kb_id=kb_id,
            name=file_name,
            title=title or file_name,
            doc_type=doc_type,
            effective_time=effective_time,
            expiration_time=expiration_time,
            created_by=created_by,
        )
        doc_info = self._row_to_doc_info(row)

        try:
            doc_id, chunks = self.document_loader.load_and_split(
                file_path=file_path,
                file_name=file_name,
                doc_id=doc_info.id,
                title=title,
                effective_time=effective_time,
                expiration_time=expiration_time,
                parse_mode=parse_mode,
                chunk_mode=chunk_mode,
                q_column=q_column,
                a_column=a_column,
            )

            if chunks:
                docs = self.document_loader.chunks_to_documents(chunks)
                kb = self._get_or_create_kb_instance(kb_id)
                kb.add_documents(docs)

            self.metadata_store.update_document(doc_info.id, vector_status="success")
            doc_info.vector_status = "success"

        except Exception as e:
            self.metadata_store.update_document(doc_info.id, vector_status="failed")
            doc_info.vector_status = "failed"
            raise RuntimeError(f"文档向量化失败: {e}") from e

        return doc_info

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
        """
        创建空文档记录（不写入向量库，用于后续添加切片）

        Returns:
            DocumentInfo: 文档信息
        """
        # 校验知识库存在
        kb_info = self.metadata_store.get_knowledge_base(kb_id)
        if kb_info is None:
            raise ValueError(f"知识库不存在: {kb_id}")

        row = self.metadata_store.create_document(
            kb_id=kb_id,
            name=name,
            title=title,
            doc_type=doc_type,
            effective_time=effective_time,
            expiration_time=expiration_time,
            created_by=created_by,
        )
        return self._row_to_doc_info(row)

    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """获取单个文档信息"""
        row = self.metadata_store.get_document(doc_id)
        return self._row_to_doc_info(row) if row else None

    def list_documents(
        self,
        kb_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict:
        """分页列出知识库下的文档"""
        return self.metadata_store.list_documents(kb_id=kb_id, page=page, limit=limit)

    def update_document(
        self,
        doc_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        updated_by: str = "system",
    ) -> Optional[DocumentInfo]:
        """
        更新文档信息
        注意：更新文档信息后，需要同步更新该文档下所有切片的对应字段
        """
        row = self.metadata_store.update_document(
            doc_id=doc_id,
            name=name,
            title=title,
            effective_time=effective_time,
            expiration_time=expiration_time,
            updated_by=updated_by,
        )
        if row is None:
            return None

        # 同步更新向量库中该文档下所有切片的元数据
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id:
            try:
                kb = self._get_or_create_kb_instance(kb_id)
                all_docs = kb.list_documents()
                for doc in all_docs:
                    md = doc.metadata
                    if md.get("doc_id") == doc_id:
                        if name is not None:
                            md["name"] = name
                        if title is not None:
                            md["title"] = title
                        if effective_time is not None:
                            md["effective_time"] = effective_time
                        if expiration_time is not None:
                            md["expiration_time"] = expiration_time
                        # 更新向量库中的元数据
                        kb.update_document(doc.doc_id or "", Document(
                            content=doc.content,
                            metadata=md,
                            doc_id=doc.doc_id,
                        ))
            except Exception:
                pass  # 向量库同步失败不影响主流程

        return self._row_to_doc_info(row)

    def delete_document(self, doc_id: str) -> bool:
        """软删除文档（同时删除向量库中的数据）"""
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        success = self.metadata_store.soft_delete_document(doc_id, kb_id or "")

        if success and kb_id:
            try:
                kb = self._get_or_create_kb_instance(kb_id)
                # 删除向量库中该文档的所有切片
                all_docs = kb.list_documents()
                chunk_ids = [
                    doc.doc_id for doc in all_docs
                    if doc.metadata.get("doc_id") == doc_id
                ]
                if chunk_ids:
                    kb.delete_documents(chunk_ids)
            except Exception:
                pass

        return success

    def toggle_document(self, doc_id: str, enable: bool) -> Optional[DocumentInfo]:
        """启用/禁用文档"""
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        row = self.metadata_store.toggle_document(doc_id, enable, kb_id or "")
        if row is None:
            return None

        # 同步更新向量库中切片的启用状态
        if kb_id:
            try:
                kb = self._get_or_create_kb_instance(kb_id)
                all_docs = kb.list_documents()
                for doc in all_docs:
                    if doc.metadata.get("doc_id") == doc_id:
                        doc.metadata["bool_enable"] = 1 if enable else 0
                        kb.update_document(doc.doc_id or "", Document(
                            content=doc.content,
                            metadata=doc.metadata,
                            doc_id=doc.doc_id,
                        ))
            except Exception:
                pass

        return self._row_to_doc_info(row)

    # ==================== 切片/知识管理 ====================

    def create_chunks(
        self,
        doc_id: str,
        segments: List[dict],
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
    ) -> List[ChunkInfo]:
        """
        为文档创建切片（手动创建）

        Args:
            doc_id: 文档ID
            segments: 切片列表 [{"content": "xxx", "chunk_metadata": [...]}, ...]
            effective_time: 生效时间
            expiration_time: 失效时间

        Returns:
            List[ChunkInfo]: 创建的切片列表
        """
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id is None:
            raise ValueError(f"文档不属于任何知识库: {doc_id}")

        doc_row = self.metadata_store.get_document(doc_id)
        if doc_row is None:
            raise ValueError(f"文档不存在: {doc_id}")

        now = datetime.now().isoformat()
        chunks = []

        for i, seg in enumerate(segments):
            chunk_info = ChunkInfo(
                id=str(uuid.uuid4()),
                doc_id=doc_id,
                content=seg.get("content", ""),
                name=doc_row.get("name", ""),
                title=doc_row.get("title", ""),
                index=i,
                create_time=now,
                effective_time=effective_time or doc_row.get("effective_time"),
                expiration_time=expiration_time or doc_row.get("expiration_time"),
                bool_delete=0,
                bool_enable=1,
                page=0,
                token=len(seg.get("content", "")),
            )
            chunks.append(chunk_info)

        # 写入向量库
        if chunks:
            docs = self.document_loader.chunks_to_documents(chunks)
            kb = self._get_or_create_kb_instance(kb_id)
            kb.add_documents(docs)

        # 更新文档状态
        self.metadata_store.update_document(doc_id, vector_status="success")

        return chunks

    def get_chunk(self, chunk_id: str, doc_id: str) -> Optional[ChunkInfo]:
        """获取单个切片信息"""
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id is None:
            return None

        kb = self._get_or_create_kb_instance(kb_id)
        try:
            # 通过抽象接口按 ID 获取
            docs = kb.get_by_ids([chunk_id])
            if docs:
                doc = docs[0]
                return DocumentLoader.vector_doc_to_chunk_info(doc)
        except Exception:
            pass
        return None

    def list_chunks(
        self,
        doc_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict:
        """
        分页列出文档下的切片

        注意：从向量库中获取，对已删除的切片做过滤
        """
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id is None:
            return {"data": [], "total": 0, "page": page, "limit": limit, "has_more": False}

        doc_row = self.metadata_store.get_document(doc_id)
        kb = self._get_or_create_kb_instance(kb_id)
        all_docs = kb.list_documents()

        # 过滤出该文档的切片
        doc_chunks = [
            doc for doc in all_docs
            if doc.metadata.get("doc_id") == doc_id
            and doc.metadata.get("bool_delete", 0) == 0
        ]

        # 按索引排序
        doc_chunks.sort(key=lambda d: d.metadata.get("index", 0))

        total = len(doc_chunks)
        start = (page - 1) * limit
        end = start + limit
        page_chunks = doc_chunks[start:end]

        # 转换为 ChunkInfo
        data = []
        for doc in page_chunks:
            chunk_info = DocumentLoader.vector_doc_to_chunk_info(doc)
            if doc_row:
                chunk_info.name = doc_row.get("name", chunk_info.name)
                chunk_info.title = doc_row.get("title", chunk_info.title)
            data.append(chunk_info.to_api_dict())

        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": end < total,
        }

    def update_chunk(
        self,
        chunk_id: str,
        doc_id: str,
        content: Optional[str] = None,
        enabled: Optional[bool] = None,
        chunk_metadata: Optional[List[dict]] = None,
    ) -> Optional[ChunkInfo]:
        """更新切片内容"""
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id is None:
            return None

        kb = self._get_or_create_kb_instance(kb_id)

        # 获取现有切片
        existing = self.get_chunk(chunk_id, doc_id)
        if existing is None:
            return None

        if content is not None:
            existing.content = content
            existing.token = len(content)
        if enabled is not None:
            existing.bool_enable = 1 if enabled else 0

        # 处理 chunk_metadata
        if chunk_metadata is not None:
            for meta_item in chunk_metadata:
                name = meta_item.get("name", "")
                value = meta_item.get("value", "")
                if name == "effective_time":
                    existing.effective_time = value
                elif name == "expiration_time":
                    existing.expiration_time = value
                elif name == "A":
                    existing.answer = value

        # 更新向量库
        metadata = DocumentLoader.chunk_to_metadata(existing)

        kb.update_document(chunk_id, Document(
            content=existing.content,
            metadata=metadata,
            doc_id=chunk_id,
        ))

        # 更新文档时间
        self.metadata_store.update_document(doc_id)
        self.metadata_store.update_knowledge_base(kb_id, name=None)  # 触发 update_time 更新

        return existing

    def delete_chunk(self, chunk_id: str, doc_id: str) -> bool:
        """软删除切片（从向量库移除）"""
        kb_id = self.metadata_store.get_kb_for_document(doc_id)
        if kb_id is None:
            return False

        kb = self._get_or_create_kb_instance(kb_id)
        return kb.delete_documents([chunk_id])

    # ==================== 向量检索 ====================

    def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict:
        """
        在指定知识库中检索

        Args:
            kb_id: 知识库ID
            query: 查询文本
            top_k: 返回数量
            score_threshold: 相似度阈值
            score_threshold_enabled: 是否启用阈值过滤

        Returns:
            Dict: 检索结果
        """
        kb = self._get_or_create_kb_instance(kb_id)
        threshold = score_threshold if score_threshold_enabled else None
        results = kb.search(
            query,
            top_k=top_k,
            score_threshold=threshold,
        )

        records = []
        for result in results:
            if not isinstance(result, SearchResult):
                continue

            score = result.score
            doc = result.document
            chunk_info = DocumentLoader.vector_doc_to_chunk_info(doc)
            # 过滤已删除和未启用
            if chunk_info.bool_delete == 0 and chunk_info.bool_enable == 1:
                records.append({
                    "segment": chunk_info.to_api_dict(),
                    "score": score,
                })

        return {
            "query": {"content": query},
            "records": records,
        }

    def search_by_label(
        self,
        query: str,
        label: str = "inquiry",
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        score_threshold_enabled: bool = False,
    ) -> Dict:
        """
        按标签在多个知识库中检索（用于业务场景联合检索）

        Args:
            query: 查询文本
            label: 知识库标签
            top_k: 每个知识库返回数量
            score_threshold: 相似度阈值
            score_threshold_enabled: 是否启用阈值过滤

        Returns:
            Dict: 聚合后的检索结果
        """
        kb_list = self.metadata_store.list_knowledge_bases(limit=100, label=label)
        all_records = []

        for kb_item in kb_list.get("items", []):
            kb_id = kb_item["id"]
            if kb_item["bool_enable"] != 1:
                continue
            try:
                result = self.search(
                    kb_id=kb_id,
                    query=query,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    score_threshold_enabled=score_threshold_enabled,
                )
                all_records.extend(result.get("records", []))
            except Exception:
                continue

        # 按分数排序取 top_k
        all_records.sort(key=lambda r: r["score"], reverse=True)
        all_records = all_records[:top_k]

        return {
            "query": {"content": query},
            "records": all_records,
        }

    # ==================== 向后兼容接口 ====================

    def switch_knowledge_base(self, kb_id: str) -> BaseVectorStore:
        """切换到指定知识库（兼容旧接口）"""
        self._current_kb_id = kb_id
        return self._get_or_create_kb_instance(kb_id)

    def get_current_kb(self) -> Optional[BaseVectorStore]:
        """获取当前知识库实例（兼容旧接口）"""
        if self._current_kb_id:
            return self._get_or_create_kb_instance(self._current_kb_id)
        # 自动选择第一个
        kb_list = self.metadata_store.list_knowledge_bases(limit=1)
        items = kb_list.get("items", [])
        if items:
            self._current_kb_id = items[0]["id"]
            return self._get_or_create_kb_instance(self._current_kb_id)
        return None

    def refresh_doc_count(self, kb_id: str) -> int:
        """刷新知识库文档计数，返回更新后的数量"""
        self.metadata_store.update_kb_doc_counts(kb_id)
        kb = self.metadata_store.get_knowledge_base(kb_id)
        return kb["num_docs"] if kb else 0


# ==================== 全局单例 ====================

_kb_manager: Optional[KnowledgeBaseManager] = None


def get_kb_manager(
    vectordb_config: Optional[VectorDBConfig] = None,
    embedding_config: Optional[EmbeddingConfig] = None,
) -> KnowledgeBaseManager:
    """获取全局 KnowledgeBaseManager 实例"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager(
            vectordb_config=vectordb_config,
            embedding_config=embedding_config,
        )
    return _kb_manager


def get_current_kb() -> Optional[BaseVectorStore]:
    """便捷函数：获取当前知识库"""
    return get_kb_manager().get_current_kb()
