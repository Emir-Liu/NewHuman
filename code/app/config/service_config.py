"""
服务器相关的配置信息
管理 FastAPI 服务的启动参数、跨域设置等
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from utils.base_config import BaseConfig


class ServiceConfig(BaseConfig):
    """
    服务配置类
    
    管理 FastAPI 服务的所有配置参数：
    - 服务器主机和端口
    - 跨域设置 (CORS)
    - 调试模式
    - 文档访问控制
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化服务配置
        
        Args:
            config_path: 环境变量文件路径，默认使用 .env
        """
        super().__init__(config_path)

        self.config_path: str = config_path

        # ========== 服务器基础配置 ==========
        
        # 监听主机，默认 0.0.0.0（监听所有网卡）
        # 开发环境可设为 127.0.0.1（仅本机访问）
        self.host: str = os.getenv('SERVICE_HOST', '0.0.0.0')
        
        # 服务端口，默认 8000
        self.port: int = int(os.getenv('SERVICE_PORT', '8000'))


if __name__ == '__main__':
    # 测试配置加载
    config = ServiceConfig()
    config.show_config()
    
    print("\n" + "=" * 40)
    print("Uvicorn 配置:")
    print(config.get_uvicorn_config())
    
    print("\n" + "=" * 40)
    print("CORS 配置:")
    print(config.get_cors_config())
