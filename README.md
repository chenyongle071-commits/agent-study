# Agent Study

这是我的 Agent 应用开发学习仓库。

目标是在 30 天内做出一个可演示、可评估、可部署的 `Experiment Agent` 项目，把大模型真正接到业务系统里，而不是只停留在聊天演示。

## 项目目标

- Python 后端开发
- FastAPI 接口设计
- SQLite / Chroma 数据管理
- LLM API 调用
- Prompt Engineering
- RAG 检索问答
- 工具调用与权限控制
- LangGraph 工作流
- Agent 评估与安全防护
- Docker Compose 部署

## 当前项目

项目名称：`Experiment Agent`

项目目标：面向实验分析场景的 Agent 系统。用户可以查询实验、对比指标、检索文档、分析失败案例，Agent 会根据问题自动选择 RAG、工具调用或普通问答，并返回带依据的结果。

## 技术栈

- Python 3.10
- FastAPI
- SQLModel / SQLAlchemy
- SQLite
- Chroma
- OpenAI SDK / DeepSeek
- LangGraph
- Vue 3 + Element Plus
- Docker / Docker Compose

## 阶段进展

### 基础阶段

- `day01`：岗位调研、目标确认、项目设计、Git/GitHub 入门
- `day02`：Python 虚拟环境、类型标注、异常处理、装饰器
- `day03`：async/await、Pydantic、环境变量、HTTP、LLM 最小客户端
- `day04`：FastAPI 基础、路由、JSON、LLM 接口
- `day05`：数据库、用户 / 会话 / 消息表
- `day06`：Message、Prompt、上下文管理

### RAG 阶段

- `day07`：流式输出、结构化 JSON、超时重试
- `day08`：文档上传、解析、清洗、Chunk 切分
- `day09`：Embedding、向量化、入库
- `day10`：Retriever、Top-K 召回、基础 RAG
- `day11`：关键词检索 + 向量检索、引用来源
- `day12`：文档更新、重复内容、拒答策略、数据隔离

### 评估与工具阶段

- `day13_14`：RAG 评估题库与评测脚本
- `day15`：真实工具：查询实验
- `day16`：失败案例工具、指标变化工具、文档检索工具、参数校验
- `day17`：LangGraph State / Node / Edge，问题分类
- `day18`：Agent 主工作流、条件路由、状态持久化
- `day19`：多轮会话 Memory、工具失败重试、日志记录
- `day20`：超时、降级、二次确认、幂等性

### 安全与部署阶段

- `day21_mcp_demo`：MCP 工具暴露与调用
- `day22_frontend`：Vue 对话页面
- `day23_frontend`：工程化前端重构
- `day24`：Prompt Injection、防越权、白名单、脱敏、危险操作确认
- `day25_eval_tools`：工具选择 / 参数 / 完成率评估
- `day26_rag_eval`：RAG 召回、事实一致性、延迟、Token 成本评估
- `day27`：Docker Compose、环境变量管理、数据初始化、健康检查

## 推荐入口

如果你想看当前最新可运行版本，直接进入：

```text
day27/
```

启动方式见：

```text
day27/README.md
```

## 学习方向

我当前主攻方向是 Agent 应用开发类实习，不以论文产出或模型训练为主线。

重点目标是掌握如何把大模型接入真实业务系统，包括：

- 会写后端接口
- 会管理数据库和历史记录
- 会构建 RAG 检索问答
- 会实现受控工具调用
- 会用 Workflow 编排 Agent 流程
- 会做基础评测、安全和部署
