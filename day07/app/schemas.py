from pydantic import BaseModel, Field
from datetime import datetime


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