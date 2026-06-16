"""
日志配置
管理本地日志的存储位置和路径
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class LogConfig(BaseConfig):
    """
    日志配置类
    
    管理日志存储目录，支持：
    - 通过环境变量 LOG_DIR 自定义路径
    - 自动创建目录
    - 获取各类日志文件（如 API 日志、Graph 日志）的完整路径
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)

        # 读取配置信息
        self.config_path: str = config_path

        # 日志相关参数
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.log_folder_path: str = os.getenv('LOG_FOLDER_PATH', './logs')


if __name__ == "__main__":
    log_config: LogConfig = LogConfig()
    log_config.show_config()
