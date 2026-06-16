from langchain.tools import tool
from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from func.kb_system_langchain.factories import VectorStoreFactory
from func.kb_system_langchain.models import Document
from func.kb_system_langchain.interfaces import BaseVectorStore

# 通过工厂创建向量库实例（根据 VECTOR_STORE_TYPE 环境变量自动选择后端）
_kb: BaseVectorStore = VectorStoreFactory.create(
    store_type=VectorDBConfig().store_type,
    vectordb_config=VectorDBConfig(),
    embedding_config=EmbeddingConfig(),
)


@tool
def add_document(content: str, metadata: dict = None) -> str:
    """添加文档到知识库。
    
    Args:
        content: 文档内容
        metadata: 文档元数据，可选
    """
    doc = Document(content=content, metadata=metadata or {})
    doc_ids = _kb.add_documents([doc])
    return f"文档添加成功，ID: {doc_ids[0]}" if doc_ids else "添加失败"


@tool
def delete_document(doc_id: str) -> str:
    """删除指定ID的文档。
    
    Args:
        doc_id: 要删除的文档ID
    """
    success = _kb.delete_documents([doc_id])
    return "删除成功" if success else "删除失败"


@tool
def update_document(doc_id: str, content: str, metadata: dict = None) -> str:
    """更新指定ID的文档。
    
    Args:
        doc_id: 要更新的文档ID
        content: 新的文档内容
        metadata: 新的文档元数据，可选
    """
    document = Document(content=content, metadata=metadata or {})
    success = _kb.update_document(doc_id, document)
    return "更新成功" if success else "更新失败"


@tool
def search_knowledge(query: str, top_k: int = 5) -> list:
    """搜索知识库中的相关文档。
    
    Args:
        query: 搜索查询文本
        top_k: 返回的最相似文档数量，默认5
    """
    results = _kb.search(query, top_k=top_k)
    return [
        {
            "content": r.document.content,
            "metadata": r.document.metadata,
            "score": r.score,
        }
        for r in results
    ]


@tool
def list_documents() -> list:
    """列出知识库中的所有文档。
    
    Returns:
        文档列表，包含内容和元数据
    """
    docs = _kb.list_documents()
    return [
        {
            "id": doc.doc_id,
            "content": doc.content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]


@tool
def get_document_count() -> int:
    """获取知识库中的文档数量。
    
    Returns:
        文档数量
    """
    return _kb.doc_count


@tool
def clear_knowledge_base() -> str:
    """清空知识库中的所有文档。
    
    Returns:
        操作结果
    """
    success = _kb.clear()
    return "清空成功" if success else "清空失败"



if __name__ == '__main__':
    print('最初的数据')
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))

    print('添加数据')
    add_document.invoke(
        {
            "content": "测试文档1",
            "metadata": {}
        }
    )
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))

    print('搜索数据')
    print(search_knowledge.invoke("测试"))

    search_res = search_knowledge.invoke('测试')

    print('更新数据')
    update_document.invoke(
        {
            "doc_id": search_res[0]["metadata"]["doc_id"],
            "content": "测试文档1-更新",
            "metadata": {}
        }
    )
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))

    print('清空')
    print(clear_knowledge_base.invoke({}))
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))