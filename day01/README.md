# Agent Engineer 30-Day Project

这是一个面向 Agent/LLM 应用实习岗位的 30 天学习与作品项目。

目标不是只学概念，而是在 30 天内做出一个可以写进简历、可以演示、可以评测的 Agent 工程项目：

**Experiment Agent**

一个面向“模型实验管理与分析”的 AI Agent 系统。用户可以上传实验文档、查询实验记录、对比模型指标、查看失败案例，并让 Agent 在 RAG 与业务工具之间自动选择，最终给出带依据、可追踪、可评测的回答。

## Day 1 产物

- [JD 共性分析](docs/day01_jd_analysis.md)
- [项目功能、数据表和接口设计](docs/project_design.md)
- [30 天任务清单](TASKS.md)

## 技术路线

- Backend: Python, FastAPI, Pydantic, SQLModel/SQLAlchemy
- Database: SQLite for local development, PostgreSQL later
- LLM: OpenAI-compatible API abstraction
- RAG: document parsing, chunking, embeddings, vector search, citations, evaluation
- Agent: LangGraph state machine, tool calling, retry, checkpoint
- Frontend: Vue
- Engineering: Docker Compose, tests, logs, README, demo video

## 本周验收目标

完成一个带数据库、历史记录和流式输出的聊天服务。

