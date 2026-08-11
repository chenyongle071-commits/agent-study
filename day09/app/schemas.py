from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class ChatRequest(BaseModel):
    """前端发送给聊天接口的数据。"""

    conversation_id: int = Field(
        description="会话 ID",
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="用户发送的问题",
    )
    temperature: float = Field(
        default=0.3,
        ge=0,
        le=2,
        description="模型回答随机性",
    )

class ChatResponse(BaseModel):
    """聊天接口返回给前端的数据。"""

    answer: str
    model: str

#UserCreate：请求体，前端创建用户时传什么
class UserCreate(BaseModel):
    """创建用户时前端提交的数据。"""

    email: str = Field(
        min_length=3,
        max_length=255,
        description="用户邮箱",
    )

#UserRead：响应体，后端创建成功后返回什么
class UserRead(BaseModel):
    """返回给前端的用户数据。"""

    id: int
    email: str
    created_at: datetime

class ConversationCreate(BaseModel):
    """创建会话时前端提交的数据。"""

    user_id: int
    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=100,
        description="会话标题",
    )


class ConversationRead(BaseModel):
    """返回给前端的会话数据。"""

    id: int
    user_id: int
    title: str
    created_at: datetime

class MessageRead(BaseModel):
    """返回给前端的消息数据。"""

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

class DocumentRead(BaseModel):
    """返回给前端的文档数据。"""

    id: int
    user_id: int
    filename: str
    content_type: str
    content_hash: str
    char_count: int
    created_at: datetime


class ChunkRead(BaseModel):
    """返回给前端的 Chunk 数据。"""

    id: int
    document_id: int
    user_id: int
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    meta: dict[str, Any]
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    """文档上传后的返回数据。"""

    document: DocumentRead
    chunk_count: int
    chunks: list[ChunkRead]

class DocumentIndexResponse(BaseModel):
    """文档向量化后的返回数据。"""

    document_id: int
    indexed_chunk_count: int


class RagSearchRequest(BaseModel):
    """RAG 检索请求。"""

    user_id: int
    query: str = Field(
        min_length=1,
        max_length=1000,
        description="用户查询问题",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="返回最相关的 chunk 数量",
    )


class RagSearchResult(BaseModel):
    """单条 RAG 检索结果。"""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


class RagSearchResponse(BaseModel):
    """RAG 检索响应。"""

    results: list[RagSearchResult]
