from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

#定义一个数据库表模型，表名对应 users。
class User(SQLModel, table=True):
    """用户表。"""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Conversation(SQLModel, table=True):
    """会话表。"""

    __tablename__ = "conversations"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(default="New Conversation")
    created_at: datetime = Field(default_factory=utc_now)


class Message(SQLModel, table=True):
    """消息表。"""

    __tablename__ = "messages"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    role: str = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=utc_now)

class Document(SQLModel, table=True):
    """文档表。"""

    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    filename: str = Field(index=True)
    content_type: str
    content_hash: str = Field(index=True)
    char_count: int
    created_at: datetime = Field(default_factory=utc_now)


class Chunk(SQLModel, table=True):
    """文档切片表。"""

    __tablename__ = "chunks"

    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    chunk_index: int = Field(index=True)
    text: str
    char_start: int
    char_end: int
    meta: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    created_at: datetime = Field(default_factory=utc_now)


#id：实验编号
#user_id：这个实验属于哪个用户
#name：实验名称
#model_name：模型名称
#dataset_name：数据集名称
#accuracy：准确率
#f1：F1 分数
#latency_ms：延迟
#cost：成本
#status：实验状态，比如 completed / failed
#created_at：创建时间
class Experiment(SQLModel, table=True):
    __tablename__ = "experiments"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(index=True)
    model_name: str
    dataset_name: str
    accuracy: float
    f1: float
    latency_ms: float
    cost: float
    status: str = Field(default="completed", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)