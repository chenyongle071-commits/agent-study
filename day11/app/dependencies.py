from typing import Annotated

from fastapi import Depends
from openai import OpenAI

from app.config import Settings, get_settings


def get_llm_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OpenAI:
    """根据 .env 配置创建大模型客户端。"""
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


LLMClient = Annotated[OpenAI, Depends(get_llm_client)]