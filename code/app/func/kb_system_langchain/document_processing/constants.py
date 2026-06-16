"""文档解析与切片相关常量"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".xlsx", ".xls"}
EXCEL_EXTENSIONS = {".xlsx", ".xls"}

CHUNK_MODE_QA = "qa"
CHUNK_MODE_ROW = "row"
UPLOAD_TYPE_QA_EXCEL = "qa_excel"
DOC_TYPE_QA_EXCEL = "qa_excel"

PARSE_MODE_AUTO = "auto"
PARSE_MODE_TABLE = "table"
VALID_PARSE_MODES = {PARSE_MODE_AUTO, PARSE_MODE_TABLE}

CHUNK_MODE_AUTO = "auto"
VALID_CHUNK_MODES = {CHUNK_MODE_AUTO, CHUNK_MODE_ROW, CHUNK_MODE_QA}

QA_Q_COLUMN_ALIASES = ("Q", "q", "question", "Question", "问题", "问")
QA_A_COLUMN_ALIASES = ("A", "a", "answer", "Answer", "答案", "答")

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def is_excel(filename: str) -> bool:
    return Path(filename).suffix.lower() in EXCEL_EXTENSIONS


def normalize_parse_mode(parse_mode: str | None) -> str:
    mode = (parse_mode or "").strip().lower() or PARSE_MODE_AUTO
    if mode not in VALID_PARSE_MODES:
        raise ValueError(
            f"不支持的解析方式: {parse_mode}，可选: {', '.join(sorted(VALID_PARSE_MODES))}"
        )
    return mode


def normalize_chunk_mode(chunk_mode: str | None) -> str:
    mode = (chunk_mode or "").strip().lower() or CHUNK_MODE_AUTO
    if mode not in VALID_CHUNK_MODES:
        raise ValueError(
            f"不支持的切片方式: {chunk_mode}，可选: {', '.join(sorted(VALID_CHUNK_MODES))}"
        )
    return mode


def resolve_doc_type(file_name: str, chunk_mode: str) -> str:
    if chunk_mode == CHUNK_MODE_QA:
        return DOC_TYPE_QA_EXCEL
    return get_file_extension(file_name)
