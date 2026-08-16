# Day27 Docker Compose 工程化启动

## 今日目标

- 完成 Docker Compose
- 完成环境变量管理
- 完成数据初始化
- 完成健康检查
- 完善 README 启动说明

## 今日完成

Day27 的重点不是增加新的业务能力，而是把项目整理成更像真实工程项目的启动方式。

目标是让项目可以通过 Docker Compose 一键启动，并且把配置、数据、健康检查都规范起来。

## 目录说明

```text
day27/
├── app/
├── picture/
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 1. Docker Compose

当前使用一个 API 容器承载后端服务。

虽然这里没有拆成多个容器，但依然使用 Compose 来统一管理：

```text
构建镜像
挂载数据卷
注入环境变量
暴露端口
配置健康检查
```

启动命令：

```powershell
cd D:\agent_study\day27
docker compose up -d --build
```

停止命令：

```powershell
docker compose down
```

## 2. 环境变量管理

环境变量统一写在 `.env` 中，模板文件是 `.env.example`。

### `.env.example`

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=replace-with-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

APP_DATABASE_FILE=app.db
APP_CHROMA_DIR=chroma_db
APP_AUTO_SEED=true
APP_DEBUG_SQL=false
```

### 说明

```text
LLM_*：大模型调用配置
APP_DATABASE_FILE：SQLite 数据库文件路径
APP_CHROMA_DIR：Chroma 向量库目录
APP_AUTO_SEED：是否启动时自动写入演示数据
APP_DEBUG_SQL：是否打印 SQL 日志
```

Docker Compose 会在容器启动时把数据库和 Chroma 路径覆盖为：

```text
/app/data/app.db
/app/data/chroma_db
```

这样数据会落在 Docker volume 中，本地运行时则默认使用 day27 目录下的相对路径。

## 3. 数据初始化

启动时会自动执行：

```text
建表
初始化演示用户
初始化演示会话
初始化三条实验数据
```

这样你在 Swagger 或前端里启动后，不需要先手工造基础数据。

演示数据包含：

```text
demo@example.com
Docker Compose Demo 会话
baseline-f1
prompt-v2-f1
rag-hybrid-search
```

## 4. 健康检查

后端提供健康检查接口：

```text
GET /health
```

它会检查：

```text
服务是否可访问
数据库是否可读
```

成功返回类似：

```json
{
  "status": "ok",
  "service": "experiment-agent",
  "database": "ok"
}
```

Compose 里也配置了容器健康检查。

## 5. 运行方式

### 本地运行

先准备 `.env`：

```powershell
copy .env.example .env
```

然后启动：

```powershell
py -m uvicorn app.main:app --reload
```

### Docker 运行

```powershell
docker compose up -d --build
```

访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## 6. 我学到的东西

Day27 让我更清楚一个工程项目的基本边界：

```text
代码负责业务
环境变量负责配置
Docker 负责部署
初始化负责开箱可用
健康检查负责确认服务状态
```

这一步做完，项目就不只是“我本机能跑”，而是更接近可以交付和复用的工程形态。

## 实际验证

本次已完成验证：

```text
GET /health
```

返回：

```json
{
  "status": "ok",
  "service": "experiment-agent",
  "database": "ok"
}
```

Docker Desktop 中也能看到容器 `day27` 正常运行。

另外也验证了：

```text
Docker Compose 可以成功构建镜像
服务可以正常启动
数据库可以自动初始化
健康检查可以正常访问
```
