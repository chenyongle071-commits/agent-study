# 这个文件演示如何用 Python 调用真实的大模型 API。
# 国内很多模型服务支持 OpenAI 兼容接口。
# 核心配置包括 API Key、Base URL 和 Model Name。
# API Key 放在 .env 里，不写死在代码中，也不能上传到 GitHub。

#OpenAI SDK -> 帮你发请求 -> 返回模型结果

from pathlib import Path

from openai import OpenAI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


def create_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


def ask_llm(client: OpenAI, settings: Settings, question: str) -> str:
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "你是一个帮助用户学习 Agent 应用开发的助手。"},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )

    #SDK帮忙封装 HTTP 请求。
    content = response.choices[0].message.content
    return content or ""


if __name__ == "__main__":
    settings = Settings()
    client = create_client(settings)

    answer = ask_llm(
        client,
        settings,
        "用三句话解释 RAG、Function Calling 和 Agent Workflow 的区别。",
    )

    print(answer)