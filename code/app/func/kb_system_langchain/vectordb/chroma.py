"""
基于 Chroma 的向量库适配器
"""

import os
import uuid
from typing import List, Optional

from langchain_chroma import Chroma

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from utils.emb_operator_langchain import EmbOperator
from func.kb_system_langchain.models import Document, SearchResult
from func.kb_system_langchain.interfaces import BaseVectorStore
from func.kb_system_langchain.vectordb.score_utils import distance_to_similarity


class ChromaVectorStore(BaseVectorStore):
    """
    Chroma 向量库适配器
    实现 BaseVectorStore 接口，使用 Chroma 作为向量数据库后端
    """

    def __init__(
        self,
        vectordb_config: VectorDBConfig,
        embedding_config: EmbeddingConfig,
    ):
        self.db_path = vectordb_config.persist_directory
        self.embedding_operator = EmbOperator(embedding_config)

        # 初始化向量存储
        self.vectorstore: Optional[Chroma] = None
        try:
            self._init_vectorstore()
        except Exception as e:
            print(f"初始化 Chroma 向量存储失败: {e}")
            raise

    def _init_vectorstore(self) -> None:
        """初始化 Chroma 向量存储"""
        os.makedirs(self.db_path, exist_ok=True)
        self.vectorstore = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embedding_operator,
        )

    # ==================== BaseVectorStore 接口实现 ====================

    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        if not documents or self.vectorstore is None:
            return []

        texts = []
        metadatas = []
        ids = []

        # max_length = 0

        for doc in documents:
            doc_id = doc.doc_id or str(uuid.uuid4())
            ids.append(doc_id)
            # if len(doc.content) > max_length:
            #     max_length = len(doc.content)
            #     print(f'切片内容:{doc.content}\n切片长度:{len(doc.content)}\n最大长度:{max_length}')
            texts.append(doc.content)
            metadatas.append({"doc_id": doc_id, **doc.metadata})

        try:
            # for tmp_idx, tmp_text in enumerate(texts):
            #     print(f"向量{tmp_idx+1}文本: {tmp_text}\n向量{tmp_idx+1}长度: {len(tmp_text)}")
            #     self.vectorstore.add_texts(
            #         texts=[tmp_text],
            #         metadatas=[metadatas[tmp_idx]], 
            #         ids=[ids[tmp_idx]]
            #     )
            self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        except Exception:
            import traceback
            traceback.print_exc()
            return []

        return ids

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        if self.vectorstore is None:
            return False
        try:
            self.vectorstore.delete(ids=doc_ids)
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
        """向量相似度搜索，返回 SearchResult 列表（含真实相似度分数）"""
        if self.vectorstore is None:
            return []

        pairs = self.vectorstore.similarity_search_with_score(query, k=top_k)
        results: List[SearchResult] = []
        for lc_doc, distance in pairs:
            score = distance_to_similarity(distance)
            if score_threshold is not None and score < score_threshold:
                continue
            metadata = lc_doc.metadata or {}
            results.append(
                SearchResult(
                    document=Document(
                        content=lc_doc.page_content,
                        metadata=metadata,
                        doc_id=metadata.get("chunk_id") or metadata.get("doc_id"),
                    ),
                    score=score,
                )
            )
        return results

    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        if self.vectorstore is None:
            return []

        data = self.vectorstore.get()
        documents = []

        for i, content in enumerate(data.get("documents", [])):
            doc_id = data.get("ids", [])[i] if i < len(data.get("ids", [])) else None
            metadata = data.get("metadatas", [])[i] if i < len(data.get("metadatas", [])) else {}
            documents.append(Document(
                content=content,
                metadata=metadata,
                doc_id=doc_id,
            ))

        return documents

    def get_by_ids(self, ids: List[str]) -> List[Document]:
        """按ID批量获取文档"""
        if self.vectorstore is None or not ids:
            return []

        data = self.vectorstore.get(ids=ids)
        documents = []

        for i, content in enumerate(data.get("documents", [])):
            doc_id = data.get("ids", [])[i] if i < len(data.get("ids", [])) else None
            metadata = data.get("metadatas", [])[i] if i < len(data.get("metadatas", [])) else {}
            documents.append(Document(
                content=content,
                metadata=metadata,
                doc_id=doc_id,
            ))

        return documents

    def clear(self) -> bool:
        """清空向量库"""
        if self.vectorstore is None:
            return False
        try:
            data = self.vectorstore.get()
            ids = data.get("ids", [])
            if ids:
                self.vectorstore.delete(ids=ids)
            return True
        except Exception:
            return False

    @property
    def doc_count(self) -> int:
        """文档数量"""
        if self.vectorstore is None:
            return 0
        data = self.vectorstore.get()
        return len(data.get("ids", []))


if __name__ == '__main__':
    store = ChromaVectorStore(
        vectordb_config=VectorDBConfig(),
        embedding_config=EmbeddingConfig(),
    )
    print('初始文档数:', store.doc_count)
    store.add_documents([Document(content="测试文档1"), Document(content="测试文档2")])
    print('添加后文档数:', store.doc_count)
    results = store.search("测试")
    print('搜索结果:', [
        {"content": r.document.content[:50], "score": r.score}
        for r in results
    ])
    store.clear()
    print('清空后文档数:', store.doc_count)
