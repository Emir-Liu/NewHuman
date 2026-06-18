"""
Langfuse 监控配置
"""


import os

from dotenv import load_dotenv
from utils.base_config import BaseConfig

class LangfuseConfig(BaseConfig):
    """
    配置类
    """

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(config_path)

        # 读取配置信息
        self.config_path: str = config_path

        self.enabled: bool = os.getenv('LANGFUSE_ENABLED', 'false') == 'true'
        # # 下面的配置不用暴露出去，Langfuse会自动读取环境变量
        # self.secret_key: str = os.getenv('LANGFUSE_SECRET_KEY', '')
        # self.public_key: str = os.getenv('LANGFUSE_PUBLIC_KEY', '')
        # self.base_url: str = os.getenv('LANGFUSE_BASE_URL', '')


if __name__ == '__main__':
    langfuse_config: LangfuseConfig = LangfuseConfig()
    langfuse_config.show_config()
    
