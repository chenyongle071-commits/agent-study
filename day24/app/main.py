import re
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse,StreamingResponse  # <--- 1. 确保导入了 HTMLResponse
from fastapi.staticfiles import StaticFiles   # <--- 2. 【新增】必须导入 StaticFiles
from sqlmodel import Session, select

from app.document_processing import (
    build_chunk_metadata,
    calculate_content_hash,
    clean_text,
    split_text_into_chunks,
)
from app.agent_graph import classify_question, get_agent_state, run_agent
from app.models import Chunk, Conversation, Document, Experiment, Message, User
from app.prompting import build_llm_messages
from app.structured import build_json_prompt, parse_structured_answer, StructuredAnswer
from app.resilience import build_rate_limit_key, call_with_retry, rate_limiter
from app.vector_store import delete_chunk_vectors, index_chunks, search_chunks
from app.retriever import build_context_from_chunks, hybrid_retrieve_chunks, retrieve_chunks
from app.config import Settings, get_settings
from app.database import create_db_and_tables, get_session
from app.dependencies import LLMClient
from app.tool_schemas import CompareMetricInput, GetExperimentInput,CalculateMetricChangesInput,SearchExperimentDocumentsInput,QueryFailureCasesInput
from app.tools import compare_metric_tool, get_experiment_tool,calculate_metric_changes_tool,search_experiment_documents_tool,query_failure_cases_tool
from app.security import (
    check_parameter_whitelist,
    check_prompt_injection,
    check_unauthorized_tool_call,
    check_high_risk_action,
    mask_sensitive_text,
    sanitize_log_payload,
)
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
    ExperimentCreate,
    ExperimentRead,
    AgentClassifyRequest,
    AgentClassifyResponse,
    AgentRunRequest,
    AgentRunResponse,
    AgentStateResponse,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/experiments", response_model=ExperimentRead)
async def create_experiment(
    request: ExperimentCreate,
    session: DbSession,
) -> ExperimentRead:
    user = session.get(User, request.user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在。",
        )

    experiment = Experiment(
        user_id=request.user_id,
        name=request.name,
        model_name=request.model_name,
        dataset_name=request.dataset_name,
        accuracy=request.accuracy,
        f1=request.f1,
        latency_ms=request.latency_ms,
        cost=request.cost,
        status=request.status,
    )

    session.add(experiment)
    session.commit()
    session.refresh(experiment)

    if experiment.id is None:
        raise HTTPException(
            status_code=500,
            detail="实验保存失败。",
        )

    return ExperimentRead(
        id=experiment.id,
        user_id=experiment.user_id,
        name=experiment.name,
        model_name=experiment.model_name,
        dataset_name=experiment.dataset_name,
        accuracy=experiment.accuracy,
        f1=experiment.f1,
        latency_ms=experiment.latency_ms,
        cost=experiment.cost,
        status=experiment.status,
        created_at=experiment.created_at,
    )

#/tools/get-experiment
#-> 根据 experiment_id 查指定实验
#-> 自动校验 user_id 权限
@app.post("/tools/get-experiment")
async def get_experiment_api(
    request: GetExperimentInput,
    session: DbSession,
):
    return get_experiment_tool(request, session)

@app.post("/tools/compare-metric")
async def compare_metric_api(
    request: CompareMetricInput,
    session: DbSession,
):
    return compare_metric_tool(request, session)

#/tools/compare-metric
#-> 对比两个实验的指定指标
#-> 自动校验 user_id 权限
#-> metric_name 只能是 accuracy / f1 / latency_ms / cost
@app.get("/experiments/{experiment_id}", response_model=ExperimentRead)
async def get_experiment_api(
    experiment_id: int,
    user_id: int,
    session: DbSession,
) -> ExperimentRead:
    experiment = session.get(Experiment, experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="实验不存在。",
        )

    if experiment.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="无权访问该实验。",
        )

    return ExperimentRead(
        id=experiment.id,
        user_id=experiment.user_id,
        name=experiment.name,
        model_name=experiment.model_name,
        dataset_name=experiment.dataset_name,
        accuracy=experiment.accuracy,
        f1=experiment.f1,
        latency_ms=experiment.latency_ms,
        cost=experiment.cost,
        status=experiment.status,
        created_at=experiment.created_at,
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


@app.post("/tools/calculate-metric-changes")
async def calculate_metric_changes_api(
    request: CalculateMetricChangesInput,
    session: DbSession,
):
    return calculate_metric_changes_tool(request, session)

@app.post("/tools/search-experiment-documents")
async def search_experiment_documents_api(
    request: SearchExperimentDocumentsInput,
    session: DbSession,
):
    return search_experiment_documents_tool(request, session)

@app.post("/tools/query-failure-cases")
async def query_failure_cases_api(
    request: QueryFailureCasesInput,
):
    return query_failure_cases_tool(request)

@app.post("/agent/classify", response_model=AgentClassifyResponse)
async def agent_classify(
    request: AgentClassifyRequest,
) -> AgentClassifyResponse:
    result = classify_question(
        user_id=request.user_id,
        question=request.question,
    )

    return AgentClassifyResponse(
        user_id=result["user_id"],
        question=result["question"],
        route=result["route"],
    )


def extract_experiment_ids(question: str) -> list[int]:
    return [int(value) for value in re.findall(r"实验\s*(\d+)", question)]


def extract_metrics(question: str) -> list[str]:
    metrics = []

    if "accuracy" in question or "准确率" in question:
        metrics.append("accuracy")

    if "F1" in question or "f1" in question:
        metrics.append("f1")

    if "latency" in question or "延迟" in question or "更快" in question:
        metrics.append("latency_ms")

    if "cost" in question or "成本" in question:
        metrics.append("cost")

    return metrics

def build_tool_response(
    selected_tool: str,
    selected_params: dict[str, object],
    tool_call,
) -> dict[str, object]:
    try:
        raw_result = tool_call()
        if hasattr(raw_result, "model_dump"):
            raw_result = raw_result.model_dump()
    except HTTPException as error:
        raw_result = {
            "success": False,
            "status_code": error.status_code,
            "detail": error.detail,
        }

    return {
        "selected_tool": selected_tool,
        "selected_params": selected_params,
        "raw_result": raw_result,
    }


def extract_document_query(question: str) -> str:
    patterns = [
        "在实验文档里搜索",
        "搜索实验文档里关于",
        "帮我从文档中找一下",
        "从文档中找一下",
        "文档中找一下",
    ]

    query = question

    for pattern in patterns:
        query = query.replace(pattern, "")

    query = query.replace("的内容", "")
    return query.strip()


def execute_real_tool_from_question(
    user_id: int,
    question: str,
    session: Session,
) -> dict[str, object]:
    experiment_ids = extract_experiment_ids(question)
    metrics = extract_metrics(question)

    if "失败案例" in question or "失败样本" in question:
        selected_params = {
            "user_id": user_id,
            "category": "all",
            "only_failed": True,
            "limit": 5,
        }

        return build_tool_response(
            selected_tool="query_failure_cases_tool",
            selected_params=selected_params,
            tool_call=lambda: query_failure_cases_tool(
                QueryFailureCasesInput(**selected_params)
            ),
        )

    if "文档" in question or "RAG" in question or "embedding" in question or "Top-K" in question:
        selected_params = {
            "user_id": user_id,
            "query": extract_document_query(question),
            "top_k": 3,
        }

        return build_tool_response(
            selected_tool="search_experiment_documents_tool",
            selected_params=selected_params,
            tool_call=lambda: search_experiment_documents_tool(
                SearchExperimentDocumentsInput(**selected_params),
                session,
            ),
        )

    if len(experiment_ids) >= 2 and len(metrics) >= 2:
        selected_params = {
            "user_id": user_id,
            "experiment_a_id": experiment_ids[0],
            "experiment_b_id": experiment_ids[1],
            "metrics": metrics,
        }

        return build_tool_response(
            selected_tool="calculate_metric_changes_tool",
            selected_params=selected_params,
            tool_call=lambda: calculate_metric_changes_tool(
                CalculateMetricChangesInput(**selected_params),
                session,
            ),
        )

    if len(experiment_ids) >= 2:
        selected_params = {
            "user_id": user_id,
            "experiment_a_id": experiment_ids[0],
            "experiment_b_id": experiment_ids[1],
            "metric_name": metrics[0] if metrics else "f1",
        }

        return build_tool_response(
            selected_tool="compare_metric_tool",
            selected_params=selected_params,
            tool_call=lambda: compare_metric_tool(
                CompareMetricInput(**selected_params),
                session,
            ),
        )

    if len(experiment_ids) == 1:
        selected_params = {
            "user_id": user_id,
            "experiment_id": experiment_ids[0],
        }

        return build_tool_response(
            selected_tool="get_experiment_tool",
            selected_params=selected_params,
            tool_call=lambda: get_experiment_tool(
                GetExperimentInput(**selected_params),
                session,
            ),
        )

    raise HTTPException(
        status_code=400,
        detail="暂时无法从问题中识别要调用的真实工具或参数。",
    )


@app.post("/agent/run", response_model=AgentRunResponse)
async def agent_run(
    request: AgentRunRequest,
    session: DbSession,
) -> AgentRunResponse:

    
    security_result = check_prompt_injection(request.question)

    if not security_result.allowed:
        return AgentRunResponse(
            user_id=request.user_id,
            question=mask_sensitive_text(request.question),
            route="blocked",
            answer="检测到可能的 Prompt Injection 请求，已拒绝执行。",
            sources=None,
            tool_result={
                "blocked": True,
                "risk_type": security_result.risk_type,
                "reason": security_result.reason,
            },
            confirmation_status=None,
            request_id=request.request_id,
            idempotent_replay=False,
        )

    tool_security_result = check_unauthorized_tool_call(request.question)

    if not tool_security_result.allowed:
        return AgentRunResponse(
            user_id=request.user_id,
            question=mask_sensitive_text(request.question),
            route="blocked",
            answer="检测到疑似越权工具调用请求，已拒绝执行。",
            sources=None,
            tool_result={
                "blocked": True,
                "risk_type": tool_security_result.risk_type,
                "reason": tool_security_result.reason,
            },
            confirmation_status=None,
            request_id=request.request_id,
            idempotent_replay=False,
        )

    high_risk_result = check_high_risk_action(request.question)

    if not high_risk_result.allowed and not request.confirmed:
        return AgentRunResponse(
            user_id=request.user_id,
            question=mask_sensitive_text(request.question),
            route="blocked",
            answer="该操作属于高风险操作，需要人工确认后才能继续执行。",
            sources=None,
            tool_result={
                "blocked": True,
                "risk_type": high_risk_result.risk_type,
                "reason": high_risk_result.reason,
                "requires_confirmation": True,
                "executed": False,
            },
            confirmation_status="pending_confirmation",
            request_id=request.request_id,
            idempotent_replay=False,
        )


    parameter_security_result = check_parameter_whitelist(request.question)

    if not parameter_security_result.allowed:
        return AgentRunResponse(
            user_id=request.user_id,
            question=mask_sensitive_text(request.question),
            route="blocked",
            answer="检测到不允许的请求参数，已拒绝执行。",
            sources=None,
            tool_result={
                "blocked": True,
                "risk_type": parameter_security_result.risk_type,
                "reason": parameter_security_result.reason,
            },
            confirmation_status=None,
            request_id=request.request_id,
            idempotent_replay=False,
        )
    
    result = run_agent(
        user_id=request.user_id,
        question=request.question,
        thread_id=request.thread_id,
        confirmed=request.confirmed,
        request_id=request.request_id,
    )

    answer = result.get("answer")
    tool_result = result.get("tool_result")

    try:
        real_tool_call = execute_real_tool_from_question(
            user_id=request.user_id,
            question=request.question,
            session=session,
        )

        tool_result = real_tool_call
        answer = f"已选择并调用真实工具：{real_tool_call['selected_tool']}"
        result["route"] = "tool"
    except HTTPException:
        pass

    return AgentRunResponse(
        user_id=result["user_id"],
        question=mask_sensitive_text(result["question"]),
        route=result["route"],
        answer=mask_sensitive_text(answer) if answer else None,
        sources=sanitize_log_payload(result.get("sources")),
        tool_result=sanitize_log_payload(tool_result),
        confirmation_status=result.get("confirmation_status"),
        request_id=result.get("request_id"),
        idempotent_replay=bool(result.get("idempotent_replay", False)),
    )

@app.get("/agent/state/{thread_id}", response_model=AgentStateResponse)
async def agent_state(thread_id: str) -> AgentStateResponse:
    state = get_agent_state(thread_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="没有找到这个 thread_id 对应的 checkpoint。",
        )

    return AgentStateResponse(
        thread_id=thread_id,
        state=state,
    )
