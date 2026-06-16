"""文件解析器抽象基类"""

from abc import ABC, abstractmethod

from func.kb_system_langchain.document_processing.types import ParsedContent


class BaseFileParser(ABC):
    """文件解析器抽象基类"""

    @property
    @abstractmethod
    def mode(self) -> str:
        """解析模式标识"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedContent:
        """解析文件，返回文本或表格行列表"""

    def supports(self, file_path: str) -> bool:
        return True
