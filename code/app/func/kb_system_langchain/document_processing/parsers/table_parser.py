"""表格 Excel 解析器"""

from pathlib import Path

from func.kb_system_langchain.document_processing.constants import EXCEL_EXTENSIONS
from func.kb_system_langchain.document_processing.excel_reader import load_xlsx_rows
from func.kb_system_langchain.document_processing.parsers.base import BaseFileParser
from func.kb_system_langchain.document_processing.types import TableParsedContent


class TableExcelParser(BaseFileParser):
    """将 Excel 解析为行字典列表"""

    mode = "table"

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in EXCEL_EXTENSIONS

    def parse(self, file_path: str) -> TableParsedContent:
        ext = Path(file_path).suffix.lower()
        if ext not in EXCEL_EXTENSIONS:
            raise ValueError("table 解析方式仅支持 .xlsx / .xls")
        return TableParsedContent(rows=load_xlsx_rows(file_path))
