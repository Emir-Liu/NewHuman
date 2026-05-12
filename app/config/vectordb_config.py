"""
向量数据库配置
管理知识库的存储路径和持久化设置
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class VectorDBConfig(BaseConfig):
    """
    向量数据库配置类
    
    管理知识库的持久化路径和存储设置
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)
        
        # 读取配置
        self.config_path: str = config_path
        
        # 存储路径配置
        self.persist_directory: str = os.getenv(
            'KB_PERSIST_DIR', 
            './my_knowledge_bases'
        )
        
        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 可选：Chroma 特定配置
        self.collection_metadata: Optional[dict] = None
        
        # # 可选：相似度搜索配置
        # self.default_top_k: int = int(os.getenv('KB_DEFAULT_TOP_K', '5'))
        # self.similarity_threshold: float = float(
        #     os.getenv('KB_SIMILARITY_THRESHOLD', '0.0')
        # )