"""自动切片：文本→智能切分，表格→一行一切片"""

from typing import List

from func.kb_system_langchain.document_processing.constants import CHUNK_MODE_AUTO, CHUNK_MODE_ROW
from func.kb_system_langchain.document_processing.splitters.base import BaseChunkSplitter
from func.kb_system_langchain.document_processing.splitters.row_splitter import RowChunkSplitter
from func.kb_system_langchain.document_processing.splitters.text_splitter import RecursiveTextChunkSplitter
from func.kb_system_langchain.document_processing.types import (
    ChunkSegment,
    ParsedContent,
    SplitContext,
    TableParsedContent,
    TextParsedContent,
)


class AutoChunkSplitter(BaseChunkSplitter):
    """根据解析结果类型自动选择切片策略"""

    mode = CHUNK_MODE_AUTO

    def __init__(self) -> None:
        self._text_splitter = RecursiveTextChunkSplitter()
        self._row_splitter = RowChunkSplitter()

    def split(self, content: ParsedContent, context: SplitContext) -> List[ChunkSegment]:
        if isinstance(content, TextParsedContent):
            return self._text_splitter.split(content, context)
        if isinstance(content, TableParsedContent):
            segments = self._row_splitter.split(content, context)
            for seg in segments:
                if not seg.chunk_mode:
                    seg.chunk_mode = CHUNK_MODE_ROW
            return segments
        raise ValueError(f"不支持的解析结果类型: {type(content)}")
