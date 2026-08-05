# Day 1: 20 个 Agent/LLM 应用实习 JD 共性分析

检索日期：2026-08-04

说明：以下 JD 来自公开招聘页或公开岗位聚合页。岗位会过期，所以这里重点提炼“稳定出现的能力要求”，作为 30 天学习计划和项目设计依据。

## 20 个 JD 样本

| # | 公司/岗位 | 关键信号 | 来源 |
|---|---|---|---|
| 1 | American Management Association, Generative AI Intern | conversational chatbot, document search, prompt, RAG | https://www.indeed.com/viewjob?jk=d993108376d0554e |
| 2 | Techolution, Generative AI Intern | Python, LLM, RAG architecture, cloud/MLOps nice to have | https://in.indeed.com/viewjob?jk=255e71abe79de920 |
| 3 | United Airlines, Generative AI Intern | Python, SQL, LLM, prompt engineering, RAG, secure development, evaluation | https://www.grapevine.in/tal/jobs/0f95413e-9659-45b9-8e3e-123569cf5269 |
| 4 | DeHypno, AI Agent Intern | AI agents, workflows, LangChain, AutoGPT, OpenAI API, RAG | https://in.linkedin.com/jobs/view/ai-agent-intern-project-based-at-dehypno-4305251354 |
| 5 | Sanfoundry, GenAI Intern | prompts, LLM evaluation, embeddings, basic RAG, documentation | https://www.sanfoundry.com/internship/genai-intern-llms-prompting-rag/ |
| 6 | Ottometric, Intern LLM and RAGs | RAG pipeline architecture, retrieval accuracy, benchmark framework, vector DB | https://app.joinrunway.io/explore/job/cmjb17h56000nl604oh5oknkb |
| 7 | Diagonal Matrix, AI/GenAI/LLM Engineer Intern | LLM apps, RAG, embeddings, vector DB, agentic workflows, APIs, evaluation | https://www.indeed.com/viewjob?jk=cd88e83a0798af74 |
| 8 | MX1, AI Engineer Intern | AI agents, tool use, RAG, FastAPI/Flask, frontend, API integrations, guardrails | https://www.ziprecruiter.com/c/MX1/Job/Intern%2C-AI-Engineer/-in-Chicago%2CIL?jid=5aefc85c3fe419e9 |
| 9 | Swafinix, AI Agent Intern | LangGraph, LangChain, CrewAI, multi-agent workflows, APIs, automation | https://in.linkedin.com/jobs/view/ai-agent-intern-at-swafinix-technologies-private-limited-4246041058 |
| 10 | Viniyog ONE, RAG AI Intern | chunking, embeddings, vector DB, hallucination reduction, source grounding | https://bebee.com/in/jobs/rag-ai-intern-llm-vector-db-fintech-use-case-viniyog-one-west-bengal--jobrapid-174237079421163929633650 |
| 11 | MentoraX, AI Engineer Intern | RAG, reranking, evaluation, agents, guardrails, FastAPI, Pydantic, Docker, pytest | https://www.mentorax.net/en/careers/ai-engineer-intern-002/ |
| 12 | Prosper Funding, AI Engineer Intern | Python, RAG, LangGraph, function calling, GCP | https://simplify.jobs/p/cd4b7740-2222-4a4f-bfb5-9d453f50aa92/AI-Engineer-Intern |
| 13 | QuantalTech, AI Engineer Intern | LLM apps, RAG, LangChain/LlamaIndex, FastAPI/Flask, embeddings, vector DB | https://www.linkedin.com/posts/shrishti-agrawal-5523a92a2_hiring-aiengineer-internship-activity-7449698804708208640-3P60 |
| 14 | Mindful Tech Solutions, AI Engineer Intern | custom GPT bot, OpenAI/Azure OpenAI, RAG, function calling, evaluation, logging | https://www.glassdoor.com/job-listing/ai-engineer-intern-entry-level-custom-gpt-bot-llm-rag-mindful-tech-solutions-JV_IC1144394_KO0%2C53_KE54%2C76.htm?jl=1010100537302 |
| 15 | VNGGames, AI Engineer Intern | prompts, evaluation, tool calling, MCP, Python, SQL, JSON, Git, RAG nice to have | https://career.vng.com.vn/job-search/detail/6783-ai-engineer-intern-vnggames |
| 16 | Gnanalytica, Generative AI Engineer Intern | agentic workflows, LangChain/LlamaIndex/Haystack, vector DB, FastAPI + Next.js | https://in.linkedin.com/jobs/view/generative-ai-engineer-intern-at-gnanalytica-4299014795 |
| 17 | Littelfuse, AI Engineer Intern | Python 3.11, Git, Docker, Linux, LLM, embeddings, vector DB, tool/function calling | https://simplify.jobs/p/00668087-1a6e-43cc-afb7-6d4c90b78cd7/AI-Engineering-Intern |
| 18 | Ingersoll Rand, AI Engineer Intern | LLM APIs, prompt/message handling, multi-agent frameworks, function calling, RAG, Git, tests | https://in.linkedin.com/jobs/view/ai-engineer-intern-at-ingersoll-rand-4426918482 |
| 19 | Delphi Consulting, Generative AI Engineer Intern | RAG, LangChain/LlamaIndex, FastAPI, Kubernetes, Docker, monitoring, guardrails | https://www.devkarriere.com/jobs/india/new-delhi/hiring-generative-ai-engineer-intern-in-new-delhi-mragke8j2ixdrh6u |
| 20 | Innotech Vietnam, AI Engineer Intern | multi-agent platform, RAG, FastAPI, embeddings, vector search, Docker, Git/GitLab | https://www.linkedin.com/jobs/view/4327967342/ |

## 高频要求统计

| 能力 | 出现次数/20 | 你应该如何证明 |
|---|---:|---|
| Python | 18 | 类型标注、异步、异常处理、测试、清晰模块设计 |
| RAG | 19 | 文档解析、chunk、embedding、retriever、引用、Recall@K 评测 |
| LLM/Prompt Engineering | 17 | system prompt、few-shot、结构化输出、上下文管理 |
| Tool/Function Calling 或 Agent | 13 | 至少 3 个真实工具、参数校验、权限继承、失败重试 |
| FastAPI/REST API | 10 | 可运行后端、路由、依赖注入、SSE 流式输出 |
| Vector DB/Embeddings | 14 | FAISS/Chroma/Qdrant/pgvector 中至少掌握一种 |
| LangChain/LlamaIndex/LangGraph/CrewAI | 14 | LangGraph 状态机与工具路由最适合展示工程能力 |
| Evaluation/Benchmarking | 10 | RAG 召回、工具选择准确率、事实一致性、延迟、Token 成本 |
| Docker/Git/Linux/CI | 11 | Docker Compose、一键启动、清晰 README、基础测试 |
| SQL/Database | 6 | 用户、会话、消息、实验、指标、工具调用日志 |
| Security/Guardrails | 7 | Prompt Injection、防越权、参数白名单、日志脱敏 |
| Frontend/UI | 5 | Vue 对话页面、实验管理、指标图表、引用来源 |

## 结论

这类岗位不再只看“会调用 LLM API”。更有竞争力的项目需要同时证明：

1. 你能写后端服务：FastAPI、数据库、鉴权、流式接口。
2. 你能做可靠 RAG：不是上传文档聊天，而是能召回、能引用、能评测。
3. 你能做真实工具调用：工具参数校验、权限控制、失败处理，而不是让模型自由编 SQL。
4. 你能做 Agent 工作流：状态、路由、重试、日志、必要时人工确认。
5. 你能工程化交付：Docker、一键启动、测试、README、演示视频、失败案例分析。

因此本月项目应避免做泛泛的“Chat with PDF”，而是做一个有业务数据、有工具、有 RAG、有评测的 Agent 系统。

