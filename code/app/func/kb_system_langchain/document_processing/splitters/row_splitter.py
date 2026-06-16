"""表格行切片器：每行 JSON 序列化为一个切片"""

import json
from typing import List

from func.kb_system_langchain.document_processing.constants import CHUNK_MODE_ROW
from func.kb_system_langchain.document_processing.splitters.base import BaseChunkSplitter
from func.kb_system_langchain.document_processing.types import (
    ChunkSegment,
    ParsedContent,
    SplitContext,
    TableParsedContent,
)


class RowChunkSplitter(BaseChunkSplitter):
    """表格一行一切片"""

    mode = CHUNK_MODE_ROW

    def split(self, content: ParsedContent, context: SplitContext) -> List[ChunkSegment]:
        if not isinstance(content, TableParsedContent):
            raise ValueError("row 切片方式需要 table 解析结果，请指定 parse_mode=table 或上传 Excel")

        segments: List[ChunkSegment] = []
        for i, row in enumerate(content.rows):
            segments.append(ChunkSegment(
                content=json.dumps(row, ensure_ascii=False),
                index=i,
                chunk_mode=CHUNK_MODE_ROW,
            ))
        return segments
