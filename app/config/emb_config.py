"""
嵌入模型配置
管理向量嵌入模型的API设置
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class EmbeddingConfig(BaseConfig):
    """
    嵌入模型配置类
    
    支持多种嵌入模型服务：
    - openai
    - 阿里云百炼 (bailian)
    - ollama
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)
        
        # 读取配置
        self.config_path: str = config_path
        
        # 模型配置
        self.model: str = os.getenv('EMBEDDING_MODEL', '')
        self.base_url: str = os.getenv('EMBEDDING_BASE_URL', '')
        self.api_key: str = os.getenv('EMBEDDING_API_KEY', '')
        self.api_type: str = os.getenv('EMBEDDING_API_TYPE', '')

if __name__ == '__main__':
    emb_config: EmbeddingConfig = EmbeddingConfig()
    emb_config.show_config()