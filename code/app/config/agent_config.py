"""Agent 运行时配置。"""

import os

from utils.base_config import BaseConfig


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class AgentConfig(BaseConfig):
    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(config_path)
        self.config_path = config_path
        raw = os.getenv("AGENT_MAX_HISTORY_TURNS", "3").strip()
        try:
            self.max_history_turns: int = int(raw)
        except ValueError:
            self.max_history_turns = 3

        depth_raw = os.getenv("AGENT_MAX_SUBAGENT_DEPTH", "1").strip()
        try:
            self.max_subagent_depth: int = max(0, int(depth_raw))
        except ValueError:
            self.max_subagent_depth = 1

        timeout_raw = os.getenv("SUBAGENT_TIMEOUT_SEC", "120").strip()
        try:
            self.subagent_timeout_sec: float = max(1.0, float(timeout_raw))
        except ValueError:
            self.subagent_timeout_sec = 120.0

        self.conversation_memory_enabled: bool = _env_bool(
            "CONVERSATION_MEMORY_ENABLED", default=True
        )
        self.conversation_memory_dir: str = os.getenv(
            "CONVERSATION_MEMORY_DIR", "memory/conversations"
        ).strip() or "memory/conversations"


_agent_config: AgentConfig | None = None


def get_agent_config() -> AgentConfig:
    global _agent_config
    if _agent_config is None:
        _agent_config = AgentConfig()
    return _agent_config
