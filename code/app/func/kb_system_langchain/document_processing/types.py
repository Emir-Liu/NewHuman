"""文档解析与切片数据类型"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class TextParsedContent:
    """文本解析结果"""
    text: str


@dataclass
class TableParsedContent:
    """表格解析结果（行字典列表）"""
    rows: List[Dict[str, str]]


ParsedContent = Union[TextParsedContent, TableParsedContent]


@dataclass
class ChunkSegment:
    """切片中间结果（尚未转为 ChunkInfo）"""
    content: str
    index: int
    chunk_mode: str = ""
    answer: str = ""


@dataclass
class SplitContext:
    """切片上下文"""
    file_path: str = ""
    q_column: Optional[str] = None
    a_column: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
