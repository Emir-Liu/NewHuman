"""
向量数据库配置
支持多种向量库类型：chroma / milvus
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class VectorDBConfig(BaseConfig):
    """
    向量数据库配置类

    支持多种向量数据库后端：
    - chroma: 本地持久化向量库
    - milvus: 分布式向量数据库

    通过 VECTOR_STORE_TYPE 环境变量切换，默认 chroma
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)

        # 读取配置
        self.config_path: str = config_path

        # ====== 通用配置 ======
        # 向量库类型: chroma / milvus
        self.store_type: str = os.getenv('VECTOR_STORE_TYPE', 'chroma')

        # 存储路径（Chroma 使用）
        self.persist_directory: str = os.getenv(
            'KB_PERSIST_DIR',
            './my_knowledge_bases'
        )
        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        # 可选：Chroma 特定配置
        self.collection_metadata: Optional[dict] = None

        # ====== Milvus 配置 ======
        self.milvus_host: str = os.getenv('MILVUS_HOST', 'localhost')
        self.milvus_port: str = os.getenv('MILVUS_PORT', '19530')
        self.milvus_user: str = os.getenv('MILVUS_USER', '')
        self.milvus_password: str = os.getenv('MILVUS_PASSWORD', '')
        self.milvus_secure: bool = os.getenv('MILVUS_SECURE', 'false').lower() == 'true'
        self.milvus_database: str = os.getenv('MILVUS_DATABASE', 'default')

        # # 可选：相似度搜索配置
        # self.default_top_k: int = int(os.getenv('KB_DEFAULT_TOP_K', '5'))
        # self.similarity_threshold: float = float(
        #     os.getenv('KB_SIMILARITY_THRESHOLD', '0.0')
        # )

    def get_milvus_connection_args(self) -> dict:
        """获取 Milvus 连接参数"""
        args = {
            "host": self.milvus_host,
            "port": self.milvus_port,
        }
        if self.milvus_user:
            args["user"] = self.milvus_user
        if self.milvus_password:
            args["password"] = self.milvus_password
        if self.milvus_secure:
            args["secure"] = True
        return args