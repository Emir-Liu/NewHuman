"""LLM Provider 抽象基类"""

from abc import ABC, abstractmethod
from typing import Any

from config.llm_config import LLMConfig


class BaseLLMProvider(ABC):
    """LLM 后端抽象基类，子类负责创建 LangChain Chat 模型实例"""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    def get_llm(self) -> Any:
        """返回 LangChain Runnable（ChatOpenAI / ChatOllama 等）"""
