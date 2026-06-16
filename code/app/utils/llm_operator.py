"""
大模型相关操作类（兼容入口）

实现已迁移至 utils.llm，此处保留原有 import 路径。
"""

from utils.llm.operator import LLMOperator
from utils.llm.factory import LLMFactory
from utils.llm.base import BaseLLMProvider

__all__ = ["LLMOperator", "LLMFactory", "BaseLLMProvider"]


if __name__ == "__main__":
    from langchain_core.messages.ai import AIMessage

    from config.llm_config import LLMConfig

    llm_config = LLMConfig()
    llm = LLMOperator(llm_config).get_llm()
    ret_str: AIMessage = llm.invoke(input="你是谁")
    print(ret_str)
