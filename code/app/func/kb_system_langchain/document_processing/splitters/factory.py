"""切片器工厂"""

from typing import Dict, Type

from func.kb_system_langchain.document_processing.constants import (
    CHUNK_MODE_AUTO,
    CHUNK_MODE_QA,
    CHUNK_MODE_ROW,
    normalize_chunk_mode,
)
from func.kb_system_langchain.document_processing.splitters.auto_splitter import AutoChunkSplitter
from func.kb_system_langchain.document_processing.splitters.base import BaseChunkSplitter
from func.kb_system_langchain.document_processing.splitters.qa_splitter import QAChunkSplitter
from func.kb_system_langchain.document_processing.splitters.row_splitter import RowChunkSplitter
from func.kb_system_langchain.document_processing.splitters.text_splitter import RecursiveTextChunkSplitter
from func.kb_system_langchain.document_processing.types import SplitContext


class ChunkSplitterFactory:
    """
    切片器工厂

    内置:
      - auto: 文本智能切分 / 表格一行一切片
      - row: 表格一行一切片
      - qa: Q 向量化，A 入 metadata
      - text: 纯文本递归切分（可单独注册使用）

    扩展:
      ChunkSplitterFactory.register("custom", CustomSplitter)
    """

    _registry: Dict[str, Type[BaseChunkSplitter]] = {
        CHUNK_MODE_AUTO: AutoChunkSplitter,
        CHUNK_MODE_ROW: RowChunkSplitter,
        CHUNK_MODE_QA: QAChunkSplitter,
        "text": RecursiveTextChunkSplitter,
    }

    @classmethod
    def register(cls, mode: str, splitter_cls: Type[BaseChunkSplitter]) -> None:
        if not issubclass(splitter_cls, BaseChunkSplitter):
            raise TypeError(f"{splitter_cls.__name__} 必须继承 BaseChunkSplitter")
        cls._registry[mode.lower()] = splitter_cls

    @classmethod
    def create(
        cls,
        chunk_mode: str | None = None,
        context: SplitContext | None = None,
    ) -> BaseChunkSplitter:
        mode = normalize_chunk_mode(chunk_mode)
        splitter_cls = cls._registry.get(mode)
        if splitter_cls is None:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"不支持的切片方式: '{mode}'。可用: {available}")
        return splitter_cls()

    @classmethod
    def available_modes(cls) -> list[str]:
        return sorted(cls._registry.keys())
