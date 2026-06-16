"""按文件后缀自动选择解析器"""

from pathlib import Path

from func.kb_system_langchain.document_processing.constants import EXCEL_EXTENSIONS
from func.kb_system_langchain.document_processing.excel_reader import load_xlsx_rows
from func.kb_system_langchain.document_processing.parsers.base import BaseFileParser
from func.kb_system_langchain.document_processing.parsers.text_parsers import (
    DocxFileParser,
    MdFileParser,
    PdfFileParser,
    TxtFileParser,
)
from func.kb_system_langchain.document_processing.types import ParsedContent, TableParsedContent


class AutoFileParser(BaseFileParser):
    """
    自动解析：Excel → 行字典列表；其余按扩展名走文本解析器。
    """

    mode = "auto"

    _TEXT_PARSERS = (
        TxtFileParser(),
        MdFileParser(),
        PdfFileParser(),
        DocxFileParser(),
    )

    def parse(self, file_path: str) -> ParsedContent:
        ext = Path(file_path).suffix.lower()

        if ext in EXCEL_EXTENSIONS:
            return TableParsedContent(rows=load_xlsx_rows(file_path))

        for parser in self._TEXT_PARSERS:
            if parser.supports(file_path):
                return parser.parse(file_path)

        raise ValueError(f"不支持的文件类型: {ext}")
