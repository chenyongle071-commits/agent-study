from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app import models


DATABASE_FILE = Path(__file__).resolve().parents[1] / "app.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """根据 models.py 中的 SQLModel 表模型创建数据库表。"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """给 FastAPI 接口提供一次数据库操作会话。"""
    with Session(engine) as session:
        yield session