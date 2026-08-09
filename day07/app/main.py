from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse,StreamingResponse  # <--- 1. 确保导入了 HTMLResponse
from fastapi.staticfiles import StaticFiles   # <--- 2. 【新增】必须导入 StaticFiles
from sqlmodel import Session, select
from app.models import Conversation, Message, User
from app.prompting import build_llm_messages
from app.structured import build_json_prompt, parse_structured_answer, StructuredAnswer
from app.resilience import build_rate_limit_key, call_with_retry, rate_limiter


from app.config import Settings, get_settings
from app.database import create_db_and_tables, get_session
from app.dependencies import LLMClient
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationRead,
    MessageRead,
    UserCreate,
    UserRead,
)


#FastAPI 启动时先执行 create_db_and_tables()，创建数据库表，然后服务继续运行。
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(
    title="Experiment Agent API",
    version="0.1.0",
    lifespan=lifespan,
)


# <--- 3. 【新增】关键步骤：挂载静态文件目录 ---
# 这行代码告诉 FastAPI：当有人访问 URL 路径 /static 时，
# 去读取当前目录下名为 'picture' 的文件夹里的文件。
try:
    app.mount("/static", StaticFiles(directory="picture"), name="static")
except RuntimeError as e:
    print(f"警告：未能挂载静态目录 'picture'。请确保该文件夹存在且路径正确。错误: {e}")

DbSession = Annotated[Session, Depends(get_session)]


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "experiment-agent",
    }

# --- 根路径接口，用来展示图片 ---
@app.get("/", response_class=HTMLResponse)
async def show_image():
    # 这里的 src="/static/展示.png" 对应上面 mount 的路径 + 文件名
    content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>图片展示</title>
            <style>
                body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f2f5; }
                img { max-width: 90%; max-height: 90%; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px; }
            </style>
        </head>
        <h>展示图片</h>
        <body>
            <!-- 注意：文件名必须完全一致，包括后缀 -->
            <img src="/static/展示.png" alt="展示图片">
        </body>
    </html>
    """
    return content

@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: int,
    session: DbSession,
) -> list[MessageRead]:
    conversation = session.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()

    return [
        MessageRead(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        for message in messages
        if message.id is not None
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    request: ChatRequest,
    session: DbSession,
    client: LLMClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    #加限流
    rate_limiter.check(build_rate_limit_key(http_request))

    conversation = session.get(Conversation, request.conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    history_messages = session.exec(
        select(Message)
        .where(Message.conversation_id == request.conversation_id)
        .order_by(Message.created_at)
    ).all()

    llm_messages = build_llm_messages(
        history_messages=list(history_messages),
        current_message=request.message,
    )

    user_message = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message,
    )

    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    try:
        response = call_with_retry(
            lambda: client.chat.completions.create(
                model=settings.llm_model,
                messages=llm_messages,
                temperature=request.temperature,
                timeout=30,
            ),
            retries=2,
            sleep_seconds=1.0,
        )
    except Exception as error:
        print(f"LLM 调用异常类型：{type(error).__name__}")
        print(f"LLM 调用异常内容：{error}")

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

    assistant_message = Message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=answer,
    )

    session.add(assistant_message)
    session.commit()
    session.refresh(assistant_message)

    return ChatResponse(
        answer=answer,
        model=settings.llm_model,
    )

@app.post("/chat/stream")
async def chat_stream(
    http_request: Request,
    request: ChatRequest,
    session: DbSession,
    client: LLMClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    rate_limiter.check(build_rate_limit_key(http_request))

    conversation = session.get(Conversation, request.conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    history_messages = session.exec(
        select(Message)
        .where(Message.conversation_id == request.conversation_id)
        .order_by(Message.created_at)
    ).all()

    llm_messages = build_llm_messages(
        history_messages=list(history_messages),
        current_message=request.message,
    )

    user_message = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message,
    )

    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    async def event_generator():
        full_text = ""

        try:
            stream = client.chat.completions.create(
                model=settings.llm_model,
                messages=llm_messages,
                temperature=request.temperature,
                stream=True,
                timeout=30,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if not delta:
                    continue

                full_text += delta
                yield f"data: {delta}\n\n"

            assistant_message = Message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=full_text,
            )

            session.add(assistant_message)
            session.commit()
            session.refresh(assistant_message)

            yield "event: done\ndata: [DONE]\n\n"

        except Exception as error:
            print(f"LLM 流式调用异常类型：{type(error).__name__}")
            print(f"LLM 流式调用异常内容：{error}")
            yield f"event: error\ndata: LLM 服务调用失败：{error}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )

@app.post("/chat/json", response_model=StructuredAnswer)
async def chat_json(
    http_request: Request,
    request: ChatRequest,
    client: LLMClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StructuredAnswer:
    rate_limiter.check(build_rate_limit_key(http_request))

    messages = build_json_prompt(request.message)

    try:
        response = call_with_retry(
            lambda: client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.0,
                timeout=30,
            ),
            retries=2,
            sleep_seconds=1.0,
        )
    except Exception as error:
        print(f"结构化 JSON 调用异常类型：{type(error).__name__}")
        print(f"结构化 JSON 调用异常内容：{error}")
        raise HTTPException(
            status_code=502,
            detail="LLM 服务调用失败，请检查 API 配置或稍后重试。",
        ) from error

    raw_text = response.choices[0].message.content

    if not raw_text:
        raise HTTPException(
            status_code=502,
            detail="LLM 返回了空内容。",
        )

    try:
        return parse_structured_answer(raw_text)
    except Exception as error:
        print(f"JSON 解析失败：{error}")
        raise HTTPException(
            status_code=502,
            detail="模型没有返回合法 JSON。",
        ) from error

@app.post("/users", response_model=UserRead)
async def create_user(
    user: UserCreate,
    session: DbSession,
) -> UserRead:
    existing_user = session.exec(
        select(User).where(User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已经存在。",
        )

    db_user = User(email=user.email)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    if db_user.id is None:
        raise HTTPException(
            status_code=500,
            detail="用户创建失败。",
        )

    return UserRead(
        id=db_user.id,
        email=db_user.email,
        created_at=db_user.created_at,
    )

@app.post("/conversations", response_model=ConversationRead)
async def create_conversation(
    conversation: ConversationCreate,
    session: DbSession,
) -> ConversationRead:
    user = session.get(User, conversation.user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在。",
        )

    db_conversation = Conversation(
        user_id=conversation.user_id,
        title=conversation.title,
    )

    session.add(db_conversation)
    session.commit()
    session.refresh(db_conversation)

    if db_conversation.id is None:
        raise HTTPException(
            status_code=500,
            detail="会话创建失败。",
        )

    return ConversationRead(
        id=db_conversation.id,
        user_id=db_conversation.user_id,
        title=db_conversation.title,
        created_at=db_conversation.created_at,
    )