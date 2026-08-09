from datetime import datetime, timezone

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