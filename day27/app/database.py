from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app import models
from app.config import get_settings


def resolve_app_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return Path(__file__).resolve().parents[1] / path


settings = get_settings()

if settings.app_database_url:
    DATABASE_URL = settings.app_database_url
else:
    DATABASE_FILE = resolve_app_path(settings.app_database_file)
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    echo=settings.app_debug_sql,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """根据 models.py 中的 SQLModel 表模型创建数据库表。"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """给 FastAPI 接口提供一次数据库操作会话。"""
    with Session(engine) as session:
        yield session
