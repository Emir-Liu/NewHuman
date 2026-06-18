"""Nacos optional switch for local dev."""

import os
from typing import Optional

from utils.base_config import BaseConfig


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class NacosConfig(BaseConfig):
    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)
        self.config_path: Optional[str] = config_path
        self.enabled: bool = _env_bool("NACOS_ENABLED", default=False)
        self.nacos_server_addresses: str = os.getenv(
            "NACOS_SERVER_ADDRESSES", "127.0.0.1:8848"
        )
        self.nacos_namespace: str = os.getenv("NACOS_NAMESPACE", "public")
        self.nacos_service_name: str = os.getenv("NACOS_SERVICE_NAME", "ai-knowledge")
        self.nacos_group: str = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")
        self.nacos_cluster_name: str = os.getenv("NACOS_CLUSTER_NAME", "DEFAULT")
        self.nacos_weight: float = float(os.getenv("NACOS_WEIGHT", "1.0"))
