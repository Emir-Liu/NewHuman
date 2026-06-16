"""文件解析器工厂"""

from typing import Dict, Type

from func.kb_system_langchain.document_processing.constants import (
    PARSE_MODE_AUTO,
    PARSE_MODE_TABLE,
    normalize_parse_mode,
)
from func.kb_system_langchain.document_processing.parsers.auto_parser import AutoFileParser
from func.kb_system_langchain.document_processing.parsers.base import BaseFileParser
from func.kb_system_langchain.document_processing.parsers.table_parser import TableExcelParser


class ParserFactory:
    """
    文件解析器工厂

    内置:
      - auto: 按后缀默认解析
      - table: Excel 行字典列表

    扩展:
      ParserFactory.register("custom", CustomParser)
    """

    _registry: Dict[str, Type[BaseFileParser]] = {
        PARSE_MODE_AUTO: AutoFileParser,
        PARSE_MODE_TABLE: TableExcelParser,
    }

    @classmethod
    def register(cls, mode: str, parser_cls: Type[BaseFileParser]) -> None:
        if not issubclass(parser_cls, BaseFileParser):
            raise TypeError(f"{parser_cls.__name__} 必须继承 BaseFileParser")
        cls._registry[mode.lower()] = parser_cls

    @classmethod
    def create(cls, parse_mode: str | None = None) -> BaseFileParser:
        mode = normalize_parse_mode(parse_mode)
        parser_cls = cls._registry.get(mode)
        if parser_cls is None:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"不支持的解析方式: '{mode}'。可用: {available}")
        return parser_cls()

    @classmethod
    def available_modes(cls) -> list[str]:
        return sorted(cls._registry.keys())
