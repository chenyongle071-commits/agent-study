#用 httpx 请求一个公开接口，理解 GET、POST、JSON 响应。
#调用大模型 API，本质上就是一次 HTTP POST 请求。

from pathlib import Path

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

#从.env里读取api信息
class Settings(BaseSettings):
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


if __name__ == "__main__":
    settings = Settings()

    #拼请求地址
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"

    headers = {
        #把api的key当作访问钥匙
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": "你是一个简洁的技术学习助手。"},
            {"role": "user", "content": "用两句话解释 HTTP 请求是什么。"},
        ],
        "temperature": 0.3,
    }

    #用 HTTP 客户端，向 url 发送一个 POST 请求，请求头是 headers，请求体是 payload，最多等 30 秒。
    with httpx.Client(timeout=30) as client:
        response = client.post(
            url,
            headers=headers,
            json=payload,
        )

    response.raise_for_status()
    data = response.json()

    answer = data["choices"][0]["message"]["content"]
    print(answer)