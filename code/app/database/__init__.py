"""
数据库模块
提供 SQLite 持久化存储，管理知识库和文档元数据
"""
from database.knowledge_base_db import KnowledgeBaseDB, get_db

__all__ = ["KnowledgeBaseDB", "get_db"]
