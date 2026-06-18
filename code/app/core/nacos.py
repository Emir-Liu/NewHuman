"""
Nacos服务注册模块
提供服务注册、心跳和注销功能
"""

import asyncio
import os
import socket

import nacos

from config.nacos_config import NacosConfig
from utils.logger_operator import LoguruOperator

# 初始化Nacos日志记录器
logger = LoguruOperator(
    name="nacos",
    level="INFO",
    log_dir="./logs"
)

_nacos_client: nacos.NacosClient | None = None
_heartbeat_task: asyncio.Task | None = None
_nacos_config: NacosConfig | None = None


def _get_local_ip() -> str:
    """Get service IP for Nacos registration.

    Priority:
      1. NACOS_REG_IP env var (explicit override for Docker/K8s)
      2. Docker/K8s node IP via environment variable
      3. Runtime detected IP
    """
    # Allow explicit override (most reliable for containerized deployment)
    explicit = os.environ.get("NACOS_REG_IP")
    if explicit:
        return explicit

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use a LAN address rather than public DNS to avoid firewall issues
        s.connect(("192.168.0.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _get_service_metadata() -> dict:
    """Build Nacos metadata matching Spring Cloud convention."""
    hostname = os.environ.get("HOSTNAME", socket.gethostname())
    return {
        "preserved.register.source": "SPRING_CLOUD",
        "hostname": hostname,
        "python.version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
    }


async def register_service(port: int) -> None:
    """Register service to Nacos and start heartbeat."""
    global _nacos_client, _heartbeat_task, _nacos_config

    try:
        if _nacos_config is None:
            _nacos_config = NacosConfig()

        if not _nacos_config.enabled:
            logger.info("Nacos disabled (NACOS_ENABLED=false), skip registration")
            return

        cfg = _nacos_config

        logger.info(f"Connecting to Nacos: {cfg.nacos_server_addresses} namespace={cfg.nacos_namespace}")
        loop = asyncio.get_running_loop()
        _nacos_client = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: nacos.NacosClient(
                    cfg.nacos_server_addresses,
                    namespace=cfg.nacos_namespace,
                ),
            ),
            timeout=10.0,
        )
        logger.info("Nacos client created")

        assert _nacos_client is not None
        client = _nacos_client
        ip = _get_local_ip()
        metadata = _get_service_metadata()
        logger.info(
            f"Registering service: name={cfg.nacos_service_name} "
            f"ip={ip}:{port} group={cfg.nacos_group} metadata={metadata}"
        )
        await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.add_naming_instance(
                    cfg.nacos_service_name,
                    ip,
                    port,
                    group_name=cfg.nacos_group,
                    cluster_name=cfg.nacos_cluster_name,
                    weight=cfg.nacos_weight,
                    metadata=metadata,
                    ephemeral=True,
                ),
            ),
            timeout=10.0,
        )
        logger.info(f"Registered to Nacos: {cfg.nacos_service_name} @ {ip}:{port}")

        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(5)
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: client.send_heartbeat(
                                cfg.nacos_service_name,
                                ip,
                                port,
                                group_name=cfg.nacos_group,
                                cluster_name=cfg.nacos_cluster_name,
                                weight=cfg.nacos_weight,
                                ephemeral=True,
                            ),
                        ),
                        timeout=5.0,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Nacos heartbeat timeout")
                except Exception as e:
                    logger.warning(f"Nacos heartbeat failed: {e}")

        _heartbeat_task = asyncio.create_task(heartbeat())
    except Exception as e:
        logger.warning(f"Nacos registration failed (non-fatal): {e}")


async def deregister_service(port: int) -> None:
    """Deregister service from Nacos."""
    global _heartbeat_task, _nacos_config

    if _nacos_config is None:
        _nacos_config = NacosConfig()
    if not _nacos_config.enabled:
        return

    if _heartbeat_task:
        _heartbeat_task.cancel()
        _heartbeat_task = None

    if _nacos_client and _nacos_config:
        client = _nacos_client
        cfg = _nacos_config
        ip = _get_local_ip()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: client.remove_naming_instance(
                    cfg.nacos_service_name,
                    ip,
                    port,
                    group_name=cfg.nacos_group,
                    cluster_name=cfg.nacos_cluster_name,
                    ephemeral=True,
                ),
            )
            logger.info(f"Deregistered from Nacos: {cfg.nacos_service_name}")
        except Exception as e:
            logger.warning(f"Nacos deregistration failed: {e}")
