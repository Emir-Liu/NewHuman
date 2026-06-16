"""递归字符文本切片器"""

from typing import List

from func.kb_system_langchain.document_processing.constants import CHUNK_MODE_AUTO
from func.kb_system_langchain.document_processing.splitters.base import BaseChunkSplitter
from func.kb_system_langchain.document_processing.types import (
    ChunkSegment,
    ParsedContent,
    SplitContext,
    TextParsedContent,
)


class RecursiveTextChunkSplitter(BaseChunkSplitter):
    """使用 LangChain RecursiveCharacterTextSplitter 切分文本"""

    mode = "text"

    def split(self, content: ParsedContent, context: SplitContext) -> List[ChunkSegment]:
        if not isinstance(content, TextParsedContent):
            raise ValueError("text 切片器仅支持文本解析结果")

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=context.chunk_size,
            chunk_overlap=context.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", ".", "!", "?", ";", ",", " "],
        )
        parts = splitter.split_text(content.text)
        segments: List[ChunkSegment] = []
        for i, part in enumerate(parts):
            if part.strip():
                segments.append(ChunkSegment(content=part, index=i, chunk_mode=""))
        return segments


class AutoTextChunkSplitter(RecursiveTextChunkSplitter):
    """auto 模式下对文本的默认切片"""

    mode = CHUNK_MODE_AUTO
