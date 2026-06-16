"""
基于 Milvus 的向量库适配器
"""

import uuid
from typing import List, Optional

from pymilvus import Collection, connections, utility

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from utils.emb_operator_langchain import EmbOperator
from func.kb_system_langchain.models import Document, SearchResult
from func.kb_system_langchain.interfaces import BaseVectorStore


class MilvusVectorStore(BaseVectorStore):
    """
    Milvus 向量库适配器
    实现 BaseVectorStore 接口，使用 Milvus 作为向量数据库后端
    """

    # Milvus Collection Schema 配置
    VECTOR_DIM = 1536  # 默认向量维度（与 embedding 模型对应）
    INDEX_PARAMS = {
        "metric_type": "IP",  # 内积相似度
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024},
    }
    SEARCH_PARAMS = {"metric_type": "IP", "params": {"nprobe": 10}}

    def __init__(
        self,
        vectordb_config: VectorDBConfig,
        embedding_config: EmbeddingConfig,
    ):
        self.config = vectordb_config
        self.embedding_operator = EmbOperator(embedding_config)
        self.collection_name = self._get_collection_name()

        # 连接到 Milvus
        self._connect()
        self._ensure_collection()

    def _get_collection_name(self) -> str:
        """
        根据 persist_directory 生成 collection 名称
        确保不同知识库使用不同 collection
        """
        import hashlib
        path_hash = hashlib.md5(self.config.persist_directory.encode()).hexdigest()[:12]
        # 限制名称长度并符合 Milvus 命名规范
        return f"kb_{path_hash}"

    def _connect(self) -> None:
        """连接 Milvus 服务"""
        conn_args = self.config.get_milvus_connection_args()
        try:
            connections.connect(alias="default", **conn_args)
            print(f"[Milvus] 已连接到 {conn_args.get('host')}:{conn_args.get('port')}")
        except Exception as e:
            print(f"[Milvus] 连接失败: {e}，将使用本地 Chroma 作为降级方案")
            raise

    def _ensure_collection(self) -> None:
        """确保 collection 存在"""
        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

        if utility.has_collection(self.collection_name):
            return

        # 创建 Schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.VECTOR_DIM),
        ]
        schema = CollectionSchema(fields, description="知识库向量存储")

        collection = Collection(name=self.collection_name, schema=schema)
        # 创建索引
        collection.create_index(
            field_name="embedding",
            index_params=self.INDEX_PARAMS,
        )
        collection.load()
        print(f"[Milvus] Collection '{self.collection_name}' 已创建")

    def _get_collection(self) -> Collection:
        """获取 collection 实例"""
        from pymilvus import Collection
        return Collection(name=self.collection_name)

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """对文本列表进行向量化"""
        embeddings = []
        for text in texts:
            vec = self.embedding_operator.embed_query(text)
            embeddings.append(vec)
        return embeddings

    # ==================== BaseVectorStore 接口实现 ====================

    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        if not documents:
            return []

        texts = [doc.content for doc in documents]
        embeddings = self._embed_texts(texts)

        insert_data = []
        ids = []

        for doc, emb in zip(documents, embeddings):
            doc_id = doc.doc_id or str(uuid.uuid4())
            ids.append(doc_id)
            insert_data.append({
                "id": doc_id,
                "content": doc.content,
                "doc_id": doc.metadata.get("doc_id", doc_id),
                "metadata": doc.metadata,
                "embedding": emb,
            })

        try:
            collection = self._get_collection()
            # 构建列数据
            columns = {
                "id": [d["id"] for d in insert_data],
                "content": [d["content"] for d in insert_data],
                "doc_id": [d["doc_id"] for d in insert_data],
                "metadata": [d["metadata"] for d in insert_data],
                "embedding": [d["embedding"] for d in insert_data],
            }
            collection.insert(columns)
            collection.flush()
        except Exception as e:
            print(f"[Milvus] 插入文档失败: {e}")
            return []

        return ids

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        if not doc_ids:
            return False
        try:
            collection = self._get_collection()
            expr = f"id in {doc_ids}"
            collection.delete(expr)
            collection.flush()
            return True
        except Exception:
            return False

    def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档（先删除再添加）"""
        self.delete_documents([doc_id])
        document.doc_id = doc_id
        new_ids = self.add_documents([document])
        return len(new_ids) > 0

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """向量相似度搜索，返回 SearchResult 列表（IP 内积作相似度）"""
        query_vector = self._embed_texts([query])[0]

        try:
            collection = self._get_collection()
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=self.SEARCH_PARAMS,
                limit=top_k,
                output_fields=["content", "doc_id", "metadata"],
            )

            hits: List[SearchResult] = []
            for hits_list in results:
                for hit in hits_list:
                    # metric_type=IP 时 distance 为内积，越大越相似
                    score = float(hit.distance)
                    if score_threshold is not None and score < score_threshold:
                        continue
                    metadata = hit.entity.get("metadata", {}) or {}
                    metadata["doc_id"] = hit.entity.get("doc_id", "")
                    hits.append(
                        SearchResult(
                            document=Document(
                                content=hit.entity.get("content", ""),
                                metadata=metadata,
                                doc_id=metadata.get("chunk_id") or metadata.get("doc_id"),
                            ),
                            score=score,
                        )
                    )
            return hits

        except Exception as e:
            print(f"[Milvus] 搜索失败: {e}")
            return []

    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        try:
            collection = self._get_collection()
            # 使用 query 获取所有数据（限制 max 条数避免 OOM）
            results = collection.query(
                expr="id != ''",
                output_fields=["content", "doc_id", "metadata"],
                limit=10000,
            )

            documents = []
            for item in results:
                documents.append(Document(
                    content=item.get("content", ""),
                    metadata=item.get("metadata", {}),
                    doc_id=item.get("id", ""),
                ))
            return documents

        except Exception as e:
            print(f"[Milvus] 列出文档失败: {e}")
            return []

    def get_by_ids(self, ids: List[str]) -> List[Document]:
        """按ID批量获取文档"""
        if not ids:
            return []

        try:
            collection = self._get_collection()
            expr = f"id in {ids}"
            results = collection.query(
                expr=expr,
                output_fields=["content", "doc_id", "metadata"],
            )

            documents = []
            for item in results:
                documents.append(Document(
                    content=item.get("content", ""),
                    metadata=item.get("metadata", {}),
                    doc_id=item.get("id", ""),
                ))
            return documents

        except Exception as e:
            print(f"[Milvus] 按ID获取文档失败: {e}")
            return []

    def clear(self) -> bool:
        """清空向量库"""
        try:
            collection = self._get_collection()
            collection.delete(expr="id != ''")
            collection.flush()
            return True
        except Exception:
            return False

    @property
    def doc_count(self) -> int:
        """文档数量"""
        try:
            collection = self._get_collection()
            return collection.num_entities
        except Exception:
            return 0
