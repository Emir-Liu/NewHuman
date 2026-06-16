"""
知识库数据模型

定义知识库、文档、知识(切片)三种核心对象的数据结构，
以及向量检索相关的数据类型。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


# ==================== 向量库相关数据结构 ====================

@dataclass
class Document:
    """向量库文档数据结构（用于向量检索）"""
    content: str                                  # 文档内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据（含 doc_id, chunk_id 等）
    doc_id: Optional[str] = None                  # 文档ID


@dataclass
class SearchResult:
    """向量搜索结果"""
    document: Document                            # 匹配的文档
    score: float                                  # 相似度分数


# ==================== 知识库元数据模型 ====================

@dataclass
class KnowledgeBaseInfo:
    """知识库元数据信息（对应 kb_metadata 表）"""
    id: str                                       # 知识库ID (UUID4)
    name: str                                     # 知识库名称
    description: str = ""                         # 知识库描述
    num_docs: int = 0                             # 文档总数（不含已删除）
    num_docs_enable: int = 0                      # 启用文档数
    bool_enable: int = 1                          # 启用状态 1=启用 0=禁用
    bool_delete: int = 0                          # 删除状态 1=已删除
    create_time: str = ""                         # 创建时间
    update_time: str = ""                         # 更新时间
    create_by: str = ""                           # 创建人
    update_by: str = ""                           # 更新人
    label: str = "inquiry"                        # 标签 (inquiry/business_des/business_data)

    # 向后兼容别名
    @property
    def kb_id(self) -> str:
        return self.id

    @property
    def created_at(self) -> str:
        return self.create_time

    @property
    def updated_at(self) -> str:
        return self.update_time

    @property
    def doc_count(self) -> int:
        return self.num_docs

    @property
    def status(self) -> str:
        return "active" if self.bool_enable else "inactive"


# ==================== 文档元数据模型 ====================

@dataclass
class DocumentInfo:
    """文档元数据信息（对应 documents 表）"""
    id: str                                       # 文档ID (UUID4)
    name: str                                     # 文档名称
    title: str = ""                               # 文档标题
    type: str = ""                                # 文档类型（文件扩展名）
    create_time: str = ""                         # 创建时间
    create_by: str = ""                           # 创建人
    update_time: str = ""                         # 更新时间
    update_by: str = ""                           # 更新人
    effective_time: Optional[str] = None          # 生效时间
    expiration_time: Optional[str] = None         # 失效时间
    vector_status: str = "processing"             # 向量化状态 (processing/failed/success)
    bool_enable: int = 1                          # 启用状态
    bool_delete: int = 0                          # 删除状态
    position: int = 0                             # 在知识库中的序号

    @property
    def indexing_status(self) -> str:
        return self.vector_status

    @property
    def enabled(self) -> bool:
        return bool(self.bool_enable)

    @property
    def doc_metadata(self) -> List[Dict[str, str]]:
        """构建文档附属信息列表"""
        meta = []
        if self.effective_time:
            meta.append({
                "name": "effective_time",
                "cn_name": "生效时间",
                "value": self.effective_time,
                "type": "str",
            })
        if self.expiration_time:
            meta.append({
                "name": "expiration_time",
                "cn_name": "失效时间",
                "value": self.expiration_time,
                "type": "str",
            })
        if self.type == "qa_excel":
            meta.append({
                "name": "upload_type",
                "cn_name": "上传类型",
                "value": "qa_excel",
                "type": "str",
            })
        return meta


# ==================== 知识/切片模型 ====================

@dataclass
class ChunkInfo:
    """知识/切片信息（存储在向量库 metadata 中）"""
    id: str                                       # 切片ID (UUID4)
    doc_id: str                                   # 所属文档ID
    content: str                                  # 切片内容
    name: str = ""                                # 文档名称
    title: str = ""                               # 文档标题
    index: int = 0                                # 切片在文档中的索引位置
    create_time: str = ""                         # 创建时间
    effective_time: Optional[str] = None          # 生效时间
    expiration_time: Optional[str] = None         # 失效时间
    bool_delete: int = 0                          # 删除状态
    bool_enable: int = 1                          # 启用状态
    page: int = 0                                 # 页数
    token: int = 0                                # 字符数
    chunk_mode: str = ""                          # 切片模式，qa 表示 QA 问答对
    answer: str = ""                              # QA 模式下的答案（A 字段，存入向量 metadata）

    @property
    def position(self) -> int:
        return self.index

    @property
    def enabled(self) -> bool:
        return bool(self.bool_enable)

    @property
    def chunk_metadata(self) -> List[Dict[str, str]]:
        """构建切片附属信息列表"""
        meta = []
        if self.effective_time:
            meta.append({
                "name": "effective_time",
                "cn_name": "生效时间",
                "value": self.effective_time,
                "type": "str",
            })
        if self.expiration_time:
            meta.append({
                "name": "expiration_time",
                "cn_name": "失效时间",
                "value": self.expiration_time,
                "type": "str",
            })
        if self.answer:
            meta.append({
                "name": "A",
                "cn_name": "答案",
                "value": self.answer,
                "type": "str",
            })
        if self.chunk_mode:
            meta.append({
                "name": "chunk_mode",
                "cn_name": "切片模式",
                "value": self.chunk_mode,
                "type": "str",
            })
        return meta

    def to_api_dict(self) -> Dict[str, Any]:
        """转换为 API 返回格式"""
        return {
            "id": self.id,
            "position": self.index,
            "document_id": self.doc_id,
            "content": self.content,
            "enabled": self.enabled,
            "indexing_status": "success",
            "created_by": "",
            "created_at": self.create_time,
            "updated_by": "",
            "updated_at": self.create_time,
            "error": "",
            "chunk_metadata": self.chunk_metadata,
        }
