"""
知识库 API 数据模型
定义知识库、文档、切片管理的请求体和响应体
参考 Dify API 设计
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== 通用响应 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    stateCode: int = Field(..., description="状态码")
    stateMsg: str = Field(default="", description="状态信息")
    context: Any = Field(default_factory=dict, description="响应数据")


# ==================== 知识库信息模型 ====================

class KnowledgeBaseItem(BaseModel):
    """知识库信息项"""
    id: str = Field(..., description="知识库ID (UUID4)")
    name: str = Field(..., description="知识库名称")
    description: str = Field(default="", description="知识库描述")
    bool_activate: int = Field(default=1, description="启用状态 1=启用 0=禁用")
    num_docs: int = Field(default=0, description="文档总数")
    num_docs_enable: int = Field(default=0, description="启用文档数")
    created_by: str = Field(default="", description="创建人")
    created_at: str = Field(default="", description="创建时间")
    updated_by: str = Field(default="", description="更新人")
    updated_at: str = Field(default="", description="更新时间")
    label: str = Field(default="inquiry", description="标签")


class KnowledgeBaseListContext(BaseModel):
    """知识库列表上下文"""
    items: List[KnowledgeBaseItem] = Field(default_factory=list, description="知识库列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")


# ==================== 知识库管理请求 ====================

class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=5, max_length=64, description="知识库名称")
    description: str = Field(default="", max_length=1024, description="知识库描述")
    label: str = Field(default="inquiry", description="标签 inquiry/business_des/business_data")
    bool_activate: int = Field(default=1, description="创建后是否启用")


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=5, max_length=64, description="新名称")
    description: Optional[str] = Field(None, max_length=1024, description="新描述")


# ==================== 文档信息模型 ====================

class DocMetadataItem(BaseModel):
    """文档附属信息项"""
    name: str = Field(..., description="字段名")
    cn_name: str = Field(default="", description="中文名称")
    value: str = Field(default="", description="字段值")
    type: str = Field(default="str", description="字段类型")


class DocumentItem(BaseModel):
    """文档信息项"""
    id: str = Field(..., description="文档ID")
    position: int = Field(default=0, description="文档序号")
    name: str = Field(..., description="文档名称")
    extension: str = Field(default="", description="文件扩展名")
    created_by: str = Field(default="", description="创建人")
    created_at: str = Field(default="", description="创建时间")
    updated_by: str = Field(default="", description="更新人")
    updated_at: str = Field(default="", description="更新时间")
    indexing_status: str = Field(default="processing", description="向量化状态")
    error: str = Field(default="", description="错误信息")
    enabled: bool = Field(default=True, description="是否启用")
    archived: bool = Field(default=False, description="是否归档")
    doc_metadata: List[DocMetadataItem] = Field(default_factory=list, description="文档附属信息")


class DocumentListContext(BaseModel):
    """文档列表上下文"""
    data: List[DocumentItem] = Field(default_factory=list, description="文档列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    limit: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")


# ==================== 文档管理请求 ====================

class UpdateDocumentRequest(BaseModel):
    """更新文档信息请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="文档名称")
    doc_metadata: Optional[List[DocMetadataItem]] = Field(None, description="文档附属信息")


# ==================== 切片/知识模型 ====================

class ChunkMetadataItem(BaseModel):
    """切片附属信息项"""
    name: str = Field(..., description="字段名")
    cn_name: str = Field(default="", description="中文名称")
    value: str = Field(default="", description="字段值")
    type: str = Field(default="str", description="字段类型")


class SegmentInput(BaseModel):
    """创建切片输入"""
    content: str = Field(..., description="切片内容")
    chunk_metadata: List[ChunkMetadataItem] = Field(default_factory=list, description="切片附属信息")


class CreateChunksRequest(BaseModel):
    """创建切片请求"""
    segments: List[SegmentInput] = Field(..., min_length=1, description="切片列表")


class ChunkItem(BaseModel):
    """切片信息项"""
    id: str = Field(..., description="切片ID")
    position: int = Field(default=0, description="切片位置")
    document_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="切片内容")
    enabled: bool = Field(default=True, description="是否启用")
    indexing_status: str = Field(default="success", description="向量化状态")
    created_by: str = Field(default="", description="创建人")
    created_at: str = Field(default="", description="创建时间")
    updated_by: str = Field(default="", description="更新人")
    updated_at: str = Field(default="", description="更新时间")
    error: str = Field(default="", description="错误信息")
    chunk_metadata: List[ChunkMetadataItem] = Field(default_factory=list, description="附属信息")


class ChunkListContext(BaseModel):
    """切片列表上下文"""
    data: List[ChunkItem] = Field(default_factory=list, description="切片列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    limit: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")


class UpdateChunkRequest(BaseModel):
    """更新切片请求"""
    segment: Optional[Dict[str, Any]] = Field(None, description="切片数据")


# ==================== 检索模型 ====================

class RetrievalModel(BaseModel):
    """检索参数"""
    top_k: int = Field(default=5, description="返回数量")
    score_threshold: float = Field(default=1.0, description="相似度阈值")
    score_threshold_enabled: bool = Field(default=False, description="是否启用阈值过滤")


class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., min_length=1, description="查询文本")
    external_retrieval_model: Optional[RetrievalModel] = Field(
        default_factory=RetrievalModel, description="检索参数"
    )


class RetrieveRecord(BaseModel):
    """检索结果记录"""
    segment: ChunkItem = Field(..., description="匹配的切片")
    score: float = Field(..., description="相似度分数")


class RetrieveContext(BaseModel):
    """检索上下文"""
    query: Dict[str, str] = Field(default_factory=dict, description="查询信息")
    records: List[RetrieveRecord] = Field(default_factory=list, description="检索结果")
