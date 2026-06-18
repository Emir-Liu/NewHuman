"""
配置信息管理类
"""

import os

from dotenv import load_dotenv
from utils.base_config import BaseConfig

class LLMConfig(BaseConfig):
    """
    配置类
    """

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(config_path)

        # 读取配置信息
        self.config_path: str = config_path

        self.model_name: str = os.getenv('LLM_MODEL_NAME', '')
        self.base_url: str = os.getenv('LLM_MODEL_BASE_URL', '')
        api_key = os.getenv('LLM_MODEL_API_KEY', '').strip()
        if not api_key:
            api_key = os.getenv('CURSOR_API_KEY', '').strip()
        self.api_key: str = api_key
        self.api_type: str = os.getenv('LLM_MODEL_API_TYPE', '')


if __name__ == '__main__':
    llm_config: LLMConfig = LLMConfig()
    llm_config.show_config()
    
