"""
基于 Chroma 的单个知识库实现
"""

import os
import uuid
from typing import List, Optional, Any

from langchain_core.documents import Document as LangchainDocument
from langchain_community.vectorstores import Chroma

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from utils.emb_operator_openai import EmbOperator
from func.knowledgebase.base import BaseVectorStore, Document, SearchResult


class KnowledgeBase(BaseVectorStore):
    """
    单个知识库
    使用 Chroma 作为向量数据库
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
            print(f"初始化向量存储失败: {e}")
            raise
    
    def _init_vectorstore(self) -> None:
        """初始化向量存储"""
        os.makedirs(self.db_path, exist_ok=True)
        self.vectorstore = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embedding_operator,
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档（手动嵌入）"""
        # print(f"[DEBUG] add_documents 被调用, documents数量: {len(documents) if documents else 0}")

        # # 改为显式检查 is None，避免 Chroma 的 bool 行为问题
        # if not documents or self.vectorstore is None:
        #     print("[DEBUG] 返回空列表: documents为空或vectorstore为None")
        #     return []

        texts = []
        metadatas = []
        ids = []

        for doc in documents:
            doc_id = doc.doc_id or str(uuid.uuid4())
            ids.append(doc_id)
            texts.append(doc.content)
            metadatas.append({"doc_id": doc_id, **doc.metadata})

        # 添加到向量库
        try:
            # self.vectorstore.add_texts(texts=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            # print(f"[DEBUG] add_texts 调用成功")
        except Exception as e:
            # print(f"[DEBUG] 添加文档失败: {e}")
            import traceback
            traceback.print_exc()
            return []

        # print(f"[DEBUG] 返回 ids: {ids}")
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
        # 删除旧文档
        self.delete_documents([doc_id])
        
        # 添加新文档，保持相同ID
        document.doc_id = doc_id
        new_ids = self.add_documents([document])
        
        return len(new_ids) > 0
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """相似度搜索（手动嵌入查询）"""
        if self.vectorstore is None:
            return []
        

        results = self.vectorstore.similarity_search(query, k=top_k)
        return results
    
    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        if self.vectorstore is None:
            return []
        
        # 获取所有数据
        data = self.vectorstore.get()
        documents = []
        
        for i, content in enumerate(data.get("documents", [])):
            doc_id = data.get("ids", [])[i] if i < len(data.get("ids", [])) else None
            metadata = data.get("metadatas", [])[i] if i < len(data.get("metadatas", [])) else {}
            
            documents.append(Document(
                content=content,
                metadata={k: v for k, v in metadata.items() if k != "doc_id"},
                doc_id=doc_id
            ))
        
        return documents
    
    def clear(self) -> bool:
        """清空知识库"""
        if self.vectorstore is None:
            return False
        
        try:
            # 获取所有ID并删除
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
    knowledge = KnowledgeBase(vectordb_config=VectorDBConfig(), embedding_config=EmbeddingConfig())
    print('最初的数据')
    print(knowledge.doc_count)
    print(knowledge.list_documents())
    knowledge.add_documents([Document(content="测试文档1"), Document(content="测试文档2")])
    print('添加后的数据')
    print(knowledge.doc_count)
    print(knowledge.list_documents())
    print('搜索')
    print(knowledge.search("测试"))
    search_res = knowledge.search('测试')
    knowledge.update_document(
        doc_id=search_res[0].metadata['doc_id'],
        document=Document(content="测试文档1-更新")
    )
    print('更新后的数据')
    print(knowledge.doc_count)
    print(knowledge.list_documents())
    print(knowledge.clear())
    print('清空后的数据')
    print(knowledge.doc_count)
    print(knowledge.list_documents())
    print(knowledge.doc_count)