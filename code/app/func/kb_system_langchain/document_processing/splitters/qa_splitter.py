"""QA 问答切片器：Q 为 content，A 写入 answer"""

from typing import List

from func.kb_system_langchain.document_processing.constants import (
    CHUNK_MODE_QA,
    QA_A_COLUMN_ALIASES,
    QA_Q_COLUMN_ALIASES,
)
from func.kb_system_langchain.document_processing.excel_reader import (
    load_qa_pairs,
    resolve_qa_column,
)
from func.kb_system_langchain.document_processing.splitters.base import BaseChunkSplitter
from func.kb_system_langchain.document_processing.types import (
    ChunkSegment,
    ParsedContent,
    SplitContext,
    TableParsedContent,
)


class QAChunkSplitter(BaseChunkSplitter):
    """Q 向量化，A 存入 metadata"""

    mode = CHUNK_MODE_QA

    def split(self, content: ParsedContent, context: SplitContext) -> List[ChunkSegment]:
        if isinstance(content, TableParsedContent):
            return self._split_from_rows(content, context)

        if context.file_path:
            pairs = load_qa_pairs(
                context.file_path,
                q_column=context.q_column,
                a_column=context.a_column,
            )
            return [
                ChunkSegment(content=q, index=i, chunk_mode=CHUNK_MODE_QA, answer=a)
                for i, (q, a) in enumerate(pairs)
            ]

        raise ValueError("qa 切片需要 Excel 表格解析结果或有效 file_path")

    def _split_from_rows(
        self,
        content: TableParsedContent,
        context: SplitContext,
    ) -> List[ChunkSegment]:
        if not content.rows:
            return []

        sample_keys = [k for k in content.rows[0].keys() if k != "_sheet"]
        q_col = resolve_qa_column(sample_keys, QA_Q_COLUMN_ALIASES, context.q_column)
        a_col = resolve_qa_column(sample_keys, QA_A_COLUMN_ALIASES, context.a_column)

        if not q_col:
            raise ValueError(
                f"未找到 Q 列，请确保表头含 {QA_Q_COLUMN_ALIASES} 之一，或通过 q_column 指定"
            )
        if not a_col:
            raise ValueError(
                f"未找到 A 列，请确保表头含 {QA_A_COLUMN_ALIASES} 之一，或通过 a_column 指定"
            )

        segments: List[ChunkSegment] = []
        index = 0
        for row in content.rows:
            question = str(row.get(q_col, "")).strip()
            answer = str(row.get(a_col, "")).strip()
            if question:
                segments.append(ChunkSegment(
                    content=question,
                    index=index,
                    chunk_mode=CHUNK_MODE_QA,
                    answer=answer,
                ))
                index += 1
        return segments
