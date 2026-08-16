from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """后端服务的运行配置。"""

    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")
    app_database_url: str | None = Field(default=None, alias="APP_DATABASE_URL")
    app_database_file: str = Field(default="app.db", alias="APP_DATABASE_FILE")
    app_chroma_dir: str = Field(default="chroma_db", alias="APP_CHROMA_DIR")
    app_auto_seed: bool = Field(default=True, alias="APP_AUTO_SEED")
    app_debug_sql: bool = Field(default=False, alias="APP_DEBUG_SQL")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """读取并缓存配置，避免每次请求都重新读取 .env。"""
    return Settings()
