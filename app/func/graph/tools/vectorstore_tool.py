from langchain.tools import tool
from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from func.knowledgebase.knowledge_base import KnowledgeBase, Document

# 初始化知识库实例
_kb = KnowledgeBase(
    vectordb_config=VectorDBConfig(),
    embedding_config=EmbeddingConfig()
)


@tool
def add_document(content: str, metadata: dict = None) -> str:
    """将内容添加到记忆中
    
    Args:
        content: 需要记忆的内容
        metadata: 附加数据
    """
    doc = Document(content=content, metadata=metadata or {})
    doc_ids = _kb.add_documents([doc])
    return f"文档添加成功，ID: {doc_ids[0]}" if doc_ids else "添加失败"


@tool
def delete_document(doc_id: str) -> str:
    """从记忆中删除指定ID的记忆
    
    Args:
        doc_id: 要删除的记忆ID
    """
    success = _kb.delete_documents([doc_id])
    return "删除成功" if success else "删除失败"


@tool
def update_document(doc_id: str, content: str, metadata: dict = None) -> str:
    """从记忆中修改指定内容
    
    Args:
        doc_id: 要更新的记忆ID
        content: 新的记忆内容
        metadata: 新记忆的附加数据，可选
    """
    document = Document(content=content, metadata=metadata or {})
    success = _kb.update_document(doc_id, document)
    return "更新成功" if success else "更新失败"


@tool
def search_knowledge(query: str, top_k: int = 5) -> list:
    """回忆相关的记忆
    
    Args:
        query: 需要回忆的内容
        top_k: 需要回忆的内容个数
    """
    results = _kb.search(query, top_k=top_k)
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in results
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
    # knowledge = KnowledgeBase(vectordb_config=VectorDBConfig(), embedding_config=EmbeddingConfig())
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
    # knowledge.add_documents([Document(content="测试文档1"), Document(content="测试文档2")])
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
    # knowledge.update_document(
    #     doc_id=search_res[0].metadata['doc_id'],
    #     document=Document(content="测试文档1-更新")
    # )
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))

    print('清空')
    print(clear_knowledge_base.invoke({}))
    print(get_document_count.invoke({}))
    print(list_documents.invoke({}))