"""按扩展名的文本类文件解析器"""

from pathlib import Path

from func.kb_system_langchain.document_processing.parsers.base import BaseFileParser
from func.kb_system_langchain.document_processing.types import TextParsedContent


class TxtFileParser(BaseFileParser):
    mode = "txt"

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".txt"

    def parse(self, file_path: str) -> TextParsedContent:
        with open(file_path, "r", encoding="utf-8") as f:
            return TextParsedContent(text=f.read())


class MdFileParser(BaseFileParser):
    mode = "md"

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".md"

    def parse(self, file_path: str) -> TextParsedContent:
        with open(file_path, "r", encoding="utf-8") as f:
            return TextParsedContent(text=f.read())


class PdfFileParser(BaseFileParser):
    mode = "pdf"

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".pdf"

    def parse(self, file_path: str) -> TextParsedContent:
        try:
            from langchain_community.document_loaders import PyPDFLoader
        except ImportError:
            raise ImportError("请安装 pypdf: pip install pypdf")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return TextParsedContent(text="\n\n".join(page.page_content for page in pages))


class DocxFileParser(BaseFileParser):
    mode = "docx"

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".docx"

    def parse(self, file_path: str) -> TextParsedContent:
        try:
            from langchain_community.document_loaders import Docx2txtLoader
        except ImportError:
            raise ImportError("请安装 docx2txt: pip install docx2txt")
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        return TextParsedContent(text="\n\n".join(doc.page_content for doc in docs))
