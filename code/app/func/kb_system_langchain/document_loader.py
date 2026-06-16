"""
文档加载器
通过 ParserFactory + ChunkSplitterFactory 完成解析与切片编排
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from func.kb_system_langchain.models import Document, ChunkInfo
from func.kb_system_langchain.document_processing.chunk_builder import build_chunk_infos
from func.kb_system_langchain.document_processing.constants import (
    CHUNK_MODE_AUTO,
    CHUNK_MODE_QA,
    CHUNK_MODE_ROW,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DOC_TYPE_QA_EXCEL,
    EXCEL_EXTENSIONS,
    PARSE_MODE_AUTO,
    PARSE_MODE_TABLE,
    SUPPORTED_EXTENSIONS,
    UPLOAD_TYPE_QA_EXCEL,
    VALID_CHUNK_MODES,
    VALID_PARSE_MODES,
    get_file_extension,
    is_excel,
    is_supported,
    normalize_chunk_mode,
    normalize_parse_mode,
    resolve_doc_type,
)
from func.kb_system_langchain.document_processing.parsers import ParserFactory
from func.kb_system_langchain.document_processing.splitters import ChunkSplitterFactory
from func.kb_system_langchain.document_processing.types import (
    SplitContext,
    TableParsedContent,
    TextParsedContent,
)


class DocumentLoader:
    """
    文档加载编排器

    解析（ParserFactory）与切片（ChunkSplitterFactory）分离，
    由本类串联完整上传流程。
    """

    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS
    QA_EXCEL_EXTENSIONS = EXCEL_EXTENSIONS

    CHUNK_MODE_QA = CHUNK_MODE_QA
    CHUNK_MODE_ROW = CHUNK_MODE_ROW
    UPLOAD_TYPE_QA_EXCEL = UPLOAD_TYPE_QA_EXCEL
    DOC_TYPE_QA_EXCEL = DOC_TYPE_QA_EXCEL

    PARSE_MODE_AUTO = PARSE_MODE_AUTO
    PARSE_MODE_TABLE = PARSE_MODE_TABLE
    VALID_PARSE_MODES = VALID_PARSE_MODES

    CHUNK_MODE_AUTO = CHUNK_MODE_AUTO
    VALID_CHUNK_MODES = VALID_CHUNK_MODES

    DEFAULT_CHUNK_SIZE = DEFAULT_CHUNK_SIZE
    DEFAULT_CHUNK_OVERLAP = DEFAULT_CHUNK_OVERLAP

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        return is_supported(filename)

    @classmethod
    def is_qa_excel_supported(cls, filename: str) -> bool:
        return is_excel(filename)

    @classmethod
    def normalize_parse_mode(cls, parse_mode: Optional[str]) -> str:
        return normalize_parse_mode(parse_mode)

    @classmethod
    def normalize_chunk_mode(cls, chunk_mode: Optional[str]) -> str:
        return normalize_chunk_mode(chunk_mode)

    @classmethod
    def resolve_doc_type(cls, file_name: str, chunk_mode: str) -> str:
        return resolve_doc_type(file_name, chunk_mode)

    @classmethod
    def get_file_extension(cls, filename: str) -> str:
        return get_file_extension(filename)

    @classmethod
    def load_file(cls, file_path: str) -> str:
        """加载文件为纯文本（兼容旧接口）"""
        parsed = ParserFactory.create(PARSE_MODE_AUTO).parse(file_path)
        if isinstance(parsed, TextParsedContent):
            return parsed.text
        if isinstance(parsed, TableParsedContent):
            import json
            return "\n\n".join(json.dumps(r, ensure_ascii=False) for r in parsed.rows)
        raise ValueError("无法将解析结果转为文本")

    @staticmethod
    def chunk_to_metadata(chunk: ChunkInfo) -> Dict[str, object]:
        metadata: Dict[str, object] = {
            "chunk_id": chunk.id,
            "doc_id": chunk.doc_id,
            "name": chunk.name,
            "title": chunk.title,
            "index": chunk.index,
            "create_time": chunk.create_time,
            "effective_time": chunk.effective_time or "",
            "expiration_time": chunk.expiration_time or "",
            "bool_delete": chunk.bool_delete,
            "bool_enable": chunk.bool_enable,
            "page": chunk.page,
            "token": chunk.token,
        }
        if chunk.chunk_mode:
            metadata["chunk_mode"] = chunk.chunk_mode
            if chunk.chunk_mode == CHUNK_MODE_QA:
                metadata["upload_type"] = UPLOAD_TYPE_QA_EXCEL
        if chunk.answer:
            metadata["A"] = chunk.answer
        return metadata

    def split_text(self, text: str) -> List[Tuple[str, int]]:
        """兼容旧接口：纯文本递归切分"""
        from func.kb_system_langchain.document_processing.splitters.text_splitter import RecursiveTextChunkSplitter

        context = SplitContext(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        segments = RecursiveTextChunkSplitter().split(
            TextParsedContent(text=text),
            context,
        )
        return [(s.content, s.index) for s in segments]

    def load_and_split(
        self,
        file_path: str,
        file_name: str,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        effective_time: Optional[str] = None,
        expiration_time: Optional[str] = None,
        parse_mode: Optional[str] = None,
        chunk_mode: Optional[str] = None,
        q_column: Optional[str] = None,
        a_column: Optional[str] = None,
    ) -> Tuple[str, List[ChunkInfo]]:
        """
        解析 + 切片完整流程。

        parse_mode: auto / table
        chunk_mode: auto / row / qa
        """
        parse_mode = normalize_parse_mode(parse_mode)
        chunk_mode = normalize_chunk_mode(chunk_mode)

        if doc_id is None:
            doc_id = str(uuid.uuid4())

        now = datetime.now().isoformat()
        title = title or file_name

        parser = ParserFactory.create(parse_mode)
        parsed = parser.parse(file_path)

        context = SplitContext(
            file_path=file_path,
            q_column=q_column,
            a_column=a_column,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        splitter = ChunkSplitterFactory.create(chunk_mode)
        segments = splitter.split(parsed, context)

        chunk_infos = build_chunk_infos(
            segments,
            doc_id=doc_id,
            file_name=file_name,
            title=title,
            effective_time=effective_time,
            expiration_time=expiration_time,
            now=now,
        )
        return doc_id, chunk_infos

    def chunks_to_documents(self, chunks: List[ChunkInfo]) -> List[Document]:
        documents = []
        for chunk in chunks:
            metadata = self.chunk_to_metadata(chunk)
            documents.append(Document(
                content=chunk.content,
                metadata=metadata,
                doc_id=chunk.id,
            ))
        return documents

    @staticmethod
    def vector_doc_to_chunk_info(doc: Document) -> ChunkInfo:
        m = doc.metadata
        return ChunkInfo(
            id=m.get("chunk_id", doc.doc_id or ""),
            doc_id=m.get("doc_id", ""),
            content=doc.content,
            name=m.get("name", ""),
            title=m.get("title", ""),
            index=m.get("index", 0),
            create_time=m.get("create_time", ""),
            effective_time=m.get("effective_time") or None,
            expiration_time=m.get("expiration_time") or None,
            bool_delete=m.get("bool_delete", 0),
            bool_enable=m.get("bool_enable", 1),
            page=m.get("page", 0),
            token=m.get("token", 0),
            chunk_mode=m.get("chunk_mode", ""),
            answer=m.get("A", ""),
        )


_default_loader: Optional[DocumentLoader] = None


def get_document_loader(
    chunk_size: int = DocumentLoader.DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DocumentLoader.DEFAULT_CHUNK_OVERLAP,
) -> DocumentLoader:
    global _default_loader
    if _default_loader is None or _default_loader.chunk_size != chunk_size:
        _default_loader = DocumentLoader(chunk_size, chunk_overlap)
    return _default_loader
