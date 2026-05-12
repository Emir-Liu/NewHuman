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
        # 加载环境变量
        if config_path is None:
            config_path = ".env"
        load_dotenv(dotenv_path=config_path, override=True)
        
        self.config_path: str = config_path

        # ========== 服务器基础配置 ==========
        
        # 监听主机，默认 0.0.0.0（监听所有网卡）
        # 开发环境可设为 127.0.0.1（仅本机访问）
        self.host: str = os.getenv('SERVICE_HOST', '0.0.0.0')
        
        # 服务端口，默认 8000
        self.port: int = int(os.getenv('SERVICE_PORT', '8000'))
        
        # 是否启用热重载（开发环境推荐开启）
        self.reload: bool = os.getenv('SERVICE_RELOAD', 'false').lower() == 'true'
        
        # 工作进程数，默认 1（开发环境），生产环境可适当增加
        self.workers: int = int(os.getenv('SERVICE_WORKERS', '1'))
        
        # 日志级别: debug/info/warning/error/critical
        self.log_level: str = os.getenv('SERVICE_LOG_LEVEL', 'info')

        # ========== 调试与安全配置 ==========
        
        # 调试模式（开发环境开启，生产环境必须关闭）
        self.debug: bool = os.getenv('SERVICE_DEBUG', 'false').lower() == 'true'
        
        # API 文档访问控制
        # 生产环境建议设为 false 或添加认证
        self.enable_docs: bool = os.getenv('SERVICE_ENABLE_DOCS', 'true').lower() == 'true'

        # ========== 跨域配置 (CORS) ==========
        
        # 是否启用 CORS
        self.cors_enabled: bool = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
        
        # 允许的源（多个用逗号分隔）
        # 开发环境: * 表示允许所有
        # 生产环境: 指定具体域名，如 https://yourdomain.com
        cors_origins = os.getenv('CORS_ALLOW_ORIGINS', '*')
        self.cors_allow_origins: List[str] = [
            origin.strip() for origin in cors_origins.split(',') if origin.strip()
        ]
        
        # 允许的 HTTP 方法（多个用逗号分隔）
        cors_methods = os.getenv('CORS_ALLOW_METHODS', '*')
        self.cors_allow_methods: List[str] = [
            method.strip() for method in cors_methods.split(',') if method.strip()
        ]
        
        # 允许的请求头（多个用逗号分隔）
        cors_headers = os.getenv('CORS_ALLOW_HEADERS', '*')
        self.cors_allow_headers: List[str] = [
            header.strip() for header in cors_headers.split(',') if header.strip()
        ]
        
        # 是否允许携带 Cookie/Authorization
        self.cors_allow_credentials: bool = os.getenv(
            'CORS_ALLOW_CREDENTIALS', 'true'
        ).lower() == 'true'
        
        # 预检请求缓存时间（秒）
        self.cors_max_age: int = int(os.getenv('CORS_MAX_AGE', '600'))

    def get_uvicorn_config(self) -> dict:
        """
        获取 Uvicorn 启动配置
        
        Returns:
            dict: Uvicorn 所需的配置字典
        """
        return {
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "workers": self.workers,
            "log_level": self.log_level,
        }

    def get_cors_config(self) -> dict:
        """
        获取 CORS 中间件配置
        
        Returns:
            dict: CORS 中间件所需的配置字典
        """
        return {
            "allow_origins": self.cors_allow_origins,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers,
            "allow_credentials": self.cors_allow_credentials,
            "max_age": self.cors_max_age,
        }


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
