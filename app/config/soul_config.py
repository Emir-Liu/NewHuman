"""
嵌入模型配置
管理向量嵌入模型的API设置
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class SoulConfig(BaseConfig):
    """
    智能体灵魂配置类

    包括:soul.md和skill相关内容
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)
        
        # 读取配置
        self.config_path: str = config_path
        
        # 模型配置
        self.md_folder: str = os.getenv('MD_FOLDER', '')

        self.soul_path: str = os.path.join(self.md_folder, 'soul.md')


if __name__ == '__main__':
    soul_config: SoulConfig = SoulConfig()
    soul_config.show_config()