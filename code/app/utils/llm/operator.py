"""LLM 操作类（兼容门面）"""

from config.llm_config import LLMConfig
from utils.llm.factory import LLMFactory


class LLMOperator:
    """大模型操作类，根据配置自动选择 LLM Provider"""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._provider = LLMFactory.create(llm_config)
        self.model = self._provider.get_llm()

    def get_llm(self):
        return self.model
