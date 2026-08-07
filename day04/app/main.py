from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.dependencies import LLMClient
from app.schemas import ChatRequest, ChatResponse


app = FastAPI(
    title="Experiment Agent API",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "experiment-agent",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    client: LLMClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个帮助用户学习 Agent 应用开发的助手。",
                },
                {
                    "role": "user",
                    "content": request.message,
                },
            ],
            temperature=request.temperature,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="LLM 服务调用失败，请检查 API 配置或稍后重试。",
        ) from error

    answer = response.choices[0].message.content

    if not answer:
        raise HTTPException(
            status_code=502,
            detail="LLM 返回了空内容。",
        )

    return ChatResponse(
        answer=answer,
        model=settings.llm_model,
    )