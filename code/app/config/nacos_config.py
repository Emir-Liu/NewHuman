"""
Nacos配置
管理Nacos服务注册相关的配置信息
"""

import os
from typing import Optional
from utils.base_config import BaseConfig


class NacosConfig(BaseConfig):
    """
    Nacos配置类

    管理 Nacos 服务注册的所有配置参数：
    - Nacos服务器地址
    - 命名空间
    - 服务名称、分组、集群名称
    - 权重配置
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化Nacos配置

        Args:
            config_path: 环境变量文件路径，默认使用 .env
        """
        super().__init__(config_path)

        self.config_path: Optional[str] = config_path

        # ========== Nacos服务器配置 ==========

        # Nacos服务器地址，格式: host:port
        self.nacos_server_addresses: str = os.getenv('NACOS_SERVER_ADDRESSES', '127.0.0.1:8848')

        # 命名空间，默认为 public
        self.nacos_namespace: str = os.getenv('NACOS_NAMESPACE', 'public')

        # ========== 服务注册配置 ==========

        # 服务名称
        self.nacos_service_name: str = os.getenv('NACOS_SERVICE_NAME', 'ai-knowledge')

        # 服务分组
        self.nacos_group: str = os.getenv('NACOS_GROUP', 'DEFAULT_GROUP')

        # 集群名称
        self.nacos_cluster_name: str = os.getenv('NACOS_CLUSTER_NAME', 'DEFAULT')

        # 服务权重，默认 1.0
        self.nacos_weight: float = float(os.getenv('NACOS_WEIGHT', '1.0'))


if __name__ == '__main__':
    # 测试配置加载
    config = NacosConfig()
    config.show_config()
