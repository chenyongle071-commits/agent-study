#API Key、Base URL、Model Name 不能硬编码在代码里。
#应该放到 .env，本地自己用，GitHub 不上传。

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-4.1-mini", alias="LLM_MODEL")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


def mask_secret(secret: str) -> str:
    if len(secret) <= 4:
        return "****"

    return secret[:4] + "..." + secret[-4:]


if __name__ == "__main__":
    settings = Settings()

    print("配置读取成功")
    print(f"LLM_BASE_URL = {settings.llm_base_url}")
    print(f"LLM_MODEL = {settings.llm_model}")
    print(f"LLM_API_KEY = {mask_secret(settings.llm_api_key)}")