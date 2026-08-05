# Agent Study

这是我的 Agent 应用开发类实习学习仓库。

目标是在 30 天内完成一个可以演示、可以写进简历的 Agent 应用项目，重点覆盖：

- Python 后端开发
- FastAPI
- Git / GitHub
- 数据库 MySQL / SQLite
- LLM API 调用
- Prompt Engineering
- RAG
- Function Calling
- LangGraph Workflow
- Vector DB
- Memory
- 项目评测与部署

## 学习方向

我当前主攻方向是 Agent 应用开发类实习，不以论文产出或模型训练为主线。

重点目标是掌握如何把大模型接入真实业务系统，包括：

- 会写后端接口
- 会管理数据库和历史记录
- 会构建 RAG 检索问答
- 会实现受控工具调用
- 会用 Workflow 编排 Agent 流程
- 会做基础评测、安全和部署

## 目录

- `day01/`：岗位调研、目标确认、项目设计、Git/GitHub 入门
- `day02/`：Python 虚拟环境、类型标注、异常处理、装饰器

## 当前项目设想

项目名称：Experiment Agent

项目目标：实现一个面向模型实验分析的 Agent 系统。用户可以查询实验、对比指标、检索文档、分析失败案例，Agent 根据问题自动选择 RAG 或工具调用，并返回带依据的回答。