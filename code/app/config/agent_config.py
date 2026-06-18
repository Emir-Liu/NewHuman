"""Agent 运行时配置。"""

import os

from utils.base_config import BaseConfig


class AgentConfig(BaseConfig):
    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(config_path)
        self.config_path = config_path
        raw = os.getenv("AGENT_MAX_HISTORY_TURNS", "3").strip()
        try:
            self.max_history_turns: int = int(raw)
        except ValueError:
            self.max_history_turns = 3


_agent_config: AgentConfig | None = None


def get_agent_config() -> AgentConfig:
    global _agent_config
    if _agent_config is None:
        _agent_config = AgentConfig()
    return _agent_config
