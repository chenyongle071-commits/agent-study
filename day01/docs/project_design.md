# 项目设计：Experiment Agent

## 项目定位

Experiment Agent 是一个“模型实验分析助手”。它模拟真实 AI 团队中的实验管理场景：

- 用户上传实验文档、日报、失败案例和指标说明。
- 用户录入不同实验的模型、数据集、指标和状态。
- 用户用自然语言提问，例如“上周失败最多的实验是什么？”、“A 模型比 B 模型 F1 提升多少？”、“这次指标下降可能是什么原因？”。
- Agent 自动判断应该走 RAG、业务工具，还是二者结合。
- 最终回答必须带依据：数据库查询结果、文档引用、工具执行日志。

## MVP 功能

### 第 1 周：聊天服务

- 用户注册/登录
- 创建会话
- 保存历史消息
- 调用 LLM
- SSE 流式输出
- 基础错误处理、超时、重试

### 第 2 周：RAG

- 上传文档
- 文档解析与清洗
- Chunk 切分
- Embedding 与向量存储
- Top-K 检索
- 答案引用来源
- RAG 评测集与 Recall@K

### 第 3 周：Agent + Tools

- 工具 1：查询指定实验
- 工具 2：对比模型指标
- 工具 3：查询失败案例
- 工具 4：计算指标变化
- 工具 5：检索实验文档
- LangGraph 路由：识别问题 -> 选择 RAG/工具 -> 执行 -> 检查充分性 -> 生成答案
- 工具失败重试、超时降级、执行日志

### 第 4 周：前端、评测、安全、部署

- Vue 对话界面
- 实验管理页面
- 指标对比图表
- 工具执行过程展示
- 引用来源展示
- Prompt Injection 防护
- 工具权限校验
- Docker Compose
- README 与 3 分钟演示

## 数据表设计

### users

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 用户 ID |
| email | string | 登录邮箱 |
| hashed_password | string | 密码哈希 |
| created_at | datetime | 创建时间 |

### conversations

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 会话 ID |
| user_id | fk | 所属用户 |
| title | string | 会话标题 |
| created_at | datetime | 创建时间 |

### messages

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 消息 ID |
| conversation_id | fk | 所属会话 |
| role | enum | user/assistant/tool/system |
| content | text/json | 消息内容 |
| token_count | integer | Token 消耗 |
| created_at | datetime | 创建时间 |

### documents

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 文档 ID |
| user_id | fk | 所属用户 |
| filename | string | 文件名 |
| content_hash | string | 去重 |
| status | enum | uploaded/parsed/indexed/failed |
| created_at | datetime | 上传时间 |

### chunks

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | Chunk ID |
| document_id | fk | 所属文档 |
| user_id | fk | 用于数据隔离 |
| text | text | Chunk 文本 |
| page | integer | 页码 |
| chunk_index | integer | 顺序 |
| embedding_id | string | 向量库 ID |
| metadata | json | 来源、页码、标签 |

### experiments

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 实验 ID |
| user_id | fk | 所属用户 |
| name | string | 实验名 |
| model_name | string | 模型 |
| dataset_name | string | 数据集 |
| status | enum | running/succeeded/failed |
| notes | text | 备注 |
| created_at | datetime | 创建时间 |

### metrics

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 指标 ID |
| experiment_id | fk | 所属实验 |
| name | string | 指标名，如 accuracy/f1/latency |
| value | float | 指标值 |
| unit | string | 单位 |

### failure_cases

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 失败案例 ID |
| experiment_id | fk | 所属实验 |
| input | text | 输入 |
| expected | text | 期望输出 |
| actual | text | 实际输出 |
| reason | text | 失败原因 |

### tool_call_logs

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer/uuid | 日志 ID |
| user_id | fk | 所属用户 |
| conversation_id | fk | 所属会话 |
| tool_name | string | 工具名 |
| arguments | json | 参数，需脱敏 |
| result_summary | text/json | 结果摘要 |
| status | enum | success/failed/timeout |
| latency_ms | integer | 延迟 |
| created_at | datetime | 创建时间 |

## API 草案

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Chat

- `POST /conversations`
- `GET /conversations`
- `GET /conversations/{conversation_id}/messages`
- `POST /chat`
- `GET /chat/stream?conversation_id=...`

### Documents/RAG

- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/index`
- `POST /rag/search`
- `POST /rag/answer`

### Experiments

- `POST /experiments`
- `GET /experiments`
- `GET /experiments/{experiment_id}`
- `POST /experiments/{experiment_id}/metrics`
- `POST /experiments/{experiment_id}/failure-cases`
- `GET /experiments/{experiment_id}/failure-cases`

### Tools

- `POST /tools/query_experiment`
- `POST /tools/compare_metrics`
- `POST /tools/query_failure_cases`
- `POST /tools/calculate_metric_delta`
- `POST /tools/search_experiment_docs`
- `GET /tool-call-logs`

### Evaluation

- `POST /eval/rag/run`
- `POST /eval/agent/run`
- `GET /eval/runs`
- `GET /eval/runs/{run_id}`

## 简历表达目标

最终项目可以写成：

> 设计并实现一个面向模型实验分析的 Agent 系统，基于 FastAPI、SQLModel、LangGraph 和 RAG 构建多轮对话、实验指标查询、失败案例分析与文档引用回答；实现工具参数校验、用户权限隔离、SSE 流式输出、工具执行日志、RAG Recall@K 与工具选择准确率评测，并通过 Docker Compose 完成部署。

