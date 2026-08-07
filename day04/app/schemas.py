from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """前端发送给聊天接口的数据。"""

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