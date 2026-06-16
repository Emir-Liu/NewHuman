

"""
对话消息 API 数据模型
定义请求体和响应体的 Pydantic 模型
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


# ==================== 请求模型 ====================

class FileInput(BaseModel):
    """文件输入模型"""
    type: Literal["image", "document", "audio", "video"] = Field(..., description="文件类型")
    transfer_method: Literal["remote_url", "local_file"] = Field(..., description="传输方式")
    url: Optional[str] = Field(None, description="远程文件URL (transfer_method=remote_url时使用)")
    upload_file_id: Optional[str] = Field(None, description="上传文件ID (transfer_method=local_file时使用)")


class ChatMessageRequest(BaseModel):
    """发送聊天消息请求"""
    inputs: Dict[str, Any] = Field(default_factory=dict, description="应用定义的变量值")
    query: str = Field(..., min_length=1, description="用户输入/问题内容")
    response_mode: Literal["streaming", "blocking"] = Field(
        default="blocking", 
        description="响应模式: streaming(流式) 或 blocking(阻塞)"
    )
    conversation_id: Optional[str] = Field(default="", description="会话ID，空字符串表示新对话")
    user: str = Field(..., min_length=1, description="用户标识符")
    files: Optional[List[FileInput]] = Field(default=None, description="多模态文件列表")
    auto_generate_name: bool = Field(default=True, description="是否自动生成对话标题")


class StopChatMessageRequest(BaseModel):
    """停止消息生成请求"""
    user: str = Field(..., description="用户标识符")



# ==================== 响应模型 ====================

class UsageInfo(BaseModel):
    """Token 使用信息"""
    prompt_tokens: int = Field(default=0, description="输入token数")
    completion_tokens: int = Field(default=0, description="输出token数")
    total_tokens: int = Field(default=0, description="总token数")
    prompt_unit_price: str = Field(default="0", description="输入单价")
    completion_unit_price: str = Field(default="0", description="输出单价")
    prompt_price: str = Field(default="0", description="输入费用")
    completion_price: str = Field(default="0", description="输出费用")
    total_price: str = Field(default="0", description="总费用")
    currency: str = Field(default="USD", description="货币单位")
    latency: float = Field(default=0.0, description="延迟(秒)")


class RetrieverResource(BaseModel):
    """RAG 检索资源"""
    position: int = Field(..., description="位置")
    dataset_id: str = Field(..., description="知识库ID")
    dataset_name: str = Field(..., description="知识库名称")
    document_id: str = Field(..., description="文档ID")
    document_name: str = Field(..., description="文档名称")
    segment_id: str = Field(..., description="片段ID")
    score: float = Field(..., description="相似度分数")
    content: str = Field(..., description="检索到的文本内容")


class ChatMessageResponse(BaseModel):
    """聊天消息响应 (Blocking 模式)"""
    event: Literal["message"] = Field(default="message", description="事件类型")
    task_id: str = Field(..., description="任务ID")
    id: str = Field(..., description="事件唯一ID")
    message_id: str = Field(..., description="消息唯一ID")
    conversation_id: str = Field(..., description="会话ID")
    mode: Literal["chat", "agent-chat"] = Field(default="chat", description="应用模式")
    answer: str = Field(..., description="完整的AI回复内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: int = Field(..., description="消息创建时间戳(Unix秒)")


class StreamingEvent(BaseModel):
    """流式事件基础模型"""
    event: str = Field(..., description="事件类型")
    task_id: str = Field(..., description="任务ID")
    id: str = Field(..., description="事件ID")
    created_at: int = Field(..., description="创建时间戳")


class MessageEvent(StreamingEvent):
    """消息事件 (流式)"""
    event: Literal["message"] = "message"
    message_id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    mode: Literal["chat", "agent-chat"] = Field(default="chat")
    answer: str = Field(..., description="当前回答片段")


class MessageEndEvent(StreamingEvent):
    """消息结束事件 (流式)"""
    event: Literal["message_end"] = "message_end"
    conversation_id: str = Field(..., description="会话ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorEvent(StreamingEvent):
    """错误事件 (流式)"""
    event: Literal["error"] = "error"
    message: str = Field(..., description="错误信息")
    status: int = Field(..., description="HTTP状态码")
    code: str = Field(..., description="错误码")


class StopResponse(BaseModel):
    """停止响应结果"""
    result: Literal["success"] = Field(..., description="操作结果")