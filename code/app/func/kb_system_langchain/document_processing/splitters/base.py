"""切片器抽象基类"""

from abc import ABC, abstractmethod
from typing import List

from func.kb_system_langchain.document_processing.types import (
    ChunkSegment,
    ParsedContent,
    SplitContext,
)


class BaseChunkSplitter(ABC):
    """切片器抽象基类"""

    @property
    @abstractmethod
    def mode(self) -> str:
        """切片模式标识"""

    @abstractmethod
    def split(self, content: ParsedContent, context: SplitContext) -> List[ChunkSegment]:
        """将解析结果切分为片段列表"""
