from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse,StreamingResponse  # <--- 1. 确保导入了 HTMLResponse
from fastapi.staticfiles import StaticFiles   # <--- 2. 【新增】必须导入 StaticFiles
from sqlmodel import Session, select

from app.document_processing import (
    build_chunk_metadata,
    calculate_content_hash,
    clean_text,
    split_text_into_chunks,
)
from app.models import Chunk, Conversation, Document, Message, User
from app.prompting import build_llm_messages
from app.structured import build_json_prompt, parse_structured_answer, StructuredAnswer
from app.resilience import build_rate_limit_key, call_with_retry, rate_limiter
from app.vector_store import delete_chunk_vectors, index_chunks, search_chunks
from app.retriever import build_context_from_chunks, hybrid_retrieve_chunks, retrieve_chunks
from app.config import Settings, get_settings
from app.database import create_db_and_tables, get_session
from app.dependencies import LLMClient
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChunkRead,
    ConversationCreate,
    ConversationRead,
    DocumentIndexResponse,
    DocumentRead,
    DocumentUploadResponse,
    MessageRead,
    RagSearchRequest,
    RagSearchResponse,
    RagSearchResult,
    UserCreate,
    UserRead,
    RagAnswerRequest,
    RagAnswerResponse,
    RagSource,
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


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    user_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
    session: DbSession,
) -> DocumentUploadResponse:
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在。",
        )

    filename = file.filename or "uploaded.txt"
    content_type = file.content_type or "text/plain"

    if not filename.endswith((".txt", ".md")):
        raise HTTPException(
            status_code=400,
            detail="当前只支持 .txt 和 .md 文件。",
        )

    raw_bytes = await file.read()

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="文件必须是 UTF-8 编码文本。",
        ) from error

    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        raise HTTPException(
            status_code=400,
            detail="文件内容为空。",
        )

    content_hash = calculate_content_hash(cleaned_text)

    same_name_documents = session.exec(
        select(Document).where(
            Document.user_id == user_id,
            Document.filename == filename,
        )
    ).all()

    for old_document in same_name_documents:
        if old_document.content_hash == content_hash:
            raise HTTPException(
                status_code=400,
                detail="该文档已经上传过。",
            )

        old_chunks = session.exec(
            select(Chunk).where(Chunk.document_id == old_document.id)
        ).all()

        old_chunk_ids = [
            chunk.id
            for chunk in old_chunks
            if chunk.id is not None
        ]

        delete_chunk_vectors(old_chunk_ids)

        for old_chunk in old_chunks:
            session.delete(old_chunk)

        session.delete(old_document)

    session.commit()

    document = Document(
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        content_hash=content_hash,
        char_count=len(cleaned_text),
    )

    session.add(document)
    session.commit()
    session.refresh(document)

    if document.id is None:
        raise HTTPException(
            status_code=500,
            detail="文档保存失败。",
        )

    raw_chunks = split_text_into_chunks(cleaned_text)

    chunk_models: list[Chunk] = []

    for index, (char_start, char_end, chunk_text) in enumerate(raw_chunks):
        chunk = Chunk(
            document_id=document.id,
            user_id=user_id,
            chunk_index=index,
            text=chunk_text,
            char_start=char_start,
            char_end=char_end,
            meta=build_chunk_metadata(
                filename=filename,
                content_type=content_type,
                chunk_index=index,
                char_start=char_start,
                char_end=char_end,
            ),
        )

        session.add(chunk)
        chunk_models.append(chunk)

    session.commit()

    for chunk in chunk_models:
        session.refresh(chunk)

    return DocumentUploadResponse(
        document=DocumentRead(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            content_type=document.content_type,
            content_hash=document.content_hash,
            char_count=document.char_count,
            created_at=document.created_at,
        ),
        chunk_count=len(chunk_models),
        chunks=[
            ChunkRead(
                id=chunk.id,
                document_id=chunk.document_id,
                user_id=chunk.user_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                meta=chunk.meta,
                created_at=chunk.created_at,
            )
            for chunk in chunk_models
            if chunk.id is not None
        ],
    )

@app.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
async def list_document_chunks(
    document_id: int,
    session: DbSession,
) -> list[ChunkRead]:
    document = session.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="文档不存在。",
        )

    chunks = session.exec(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    ).all()

    return [
        ChunkRead(
            id=chunk.id,
            document_id=chunk.document_id,
            user_id=chunk.user_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
            meta=chunk.meta,
            created_at=chunk.created_at,
        )
        for chunk in chunks
        if chunk.id is not None
    ]

@app.post("/documents/{document_id}/index", response_model=DocumentIndexResponse)
async def index_document(
    document_id: int,
    session: DbSession,
) -> DocumentIndexResponse:
    document = session.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="文档不存在。",
        )

    chunks = session.exec(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    ).all()

    chunk_payloads = [
        {
            "id": chunk.id,
            "text": chunk.text,
            "metadata": {
                **chunk.meta,
                "chunk_db_id": chunk.id,
                "document_id": chunk.document_id,
                "user_id": chunk.user_id,
            },
        }
        for chunk in chunks
        if chunk.id is not None
    ]

    indexed_count = index_chunks(chunk_payloads)

    return DocumentIndexResponse(
        document_id=document_id,
        indexed_chunk_count=indexed_count,
    )


@app.post("/rag/search", response_model=RagSearchResponse)
async def rag_search(
    request: RagSearchRequest,
) -> RagSearchResponse:
    raw_results = search_chunks(
        query=request.query,
        user_id=request.user_id,
        top_k=request.top_k,
    )

    return RagSearchResponse(
        results=[
            RagSearchResult(
                chunk_id=result["id"],
                text=result["text"],
                metadata=result["metadata"],
                distance=result["distance"],
            )
            for result in raw_results
        ]
    )

@app.post("/rag/answer", response_model=RagAnswerResponse)
async def rag_answer(
    request: RagAnswerRequest,
    client: LLMClient,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> RagAnswerResponse:
    chunks = hybrid_retrieve_chunks(
        query=request.query,
        user_id=request.user_id,
        session=session,
        top_k=request.top_k,
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="没有检索到可靠资料，无法回答这个问题。",
        )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="没有检索到相关文档内容，无法生成有依据的回答。",
        )

    context = build_context_from_chunks(chunks)

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个严谨的 RAG 问答助手。"
                        "你只能根据用户提供的资料回答问题。"
                        "如果资料中没有答案，就回答：根据当前资料无法回答。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"用户问题：{request.query}\n\n"
                        f"可参考资料：\n{context}\n\n"
                        "请根据可参考资料回答用户问题，回答要简洁。"
                    ),
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

    sources = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        sources.append(
            RagSource(
                chunk_id=chunk["id"],
                filename=metadata.get("filename", "unknown"),
                text=chunk["text"],
                distance=chunk["distance"],
                retrieval_method=chunk.get("retrieval_method", "vector"),
            )
        )

    return RagAnswerResponse(
        answer=answer,
        sources=sources,
    )

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