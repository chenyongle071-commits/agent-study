# Day04 FastAPI 基础
Python 函数
+
HTTP 路由
+
请求参数校验
+
JSON 响应
=
FastAPI 接口

## 今日完成
今天完成了 FastAPI 后端的基础搭建。

我实现了：

- 创建 FastAPI 项目结构
- 创建 `GET /health` 健康检查接口
- 创建 `POST /chat` 聊天接口
- 使用 Pydantic 校验用户发送的 JSON 数据
- 通过依赖注入读取 `.env` 配置并创建 DeepSeek Client
- 从 Swagger `/docs` 页面测试接口
- 调用真实 DeepSeek API 并返回模型回答

## FastAPI 是什么
FastAPI 是一个 Python Web 框架，用来开发后端 API。

它可以接收浏览器、前端页面或其他程序发送的 HTTP 请求，执行对应的 Python 函数，然后返回 JSON 数据。

在这个项目中，FastAPI 是 Agent 后端的入口。以后前端会把用户的问题发送给 FastAPI，FastAPI 再调用大模型、数据库、RAG 或工具，
最后把结果返回给前端。

## /health 和 /chat 的请求流程
### GET /health

`/health` 是健康检查接口，用来确认后端服务是否已经正常启动。

请求流程：

```text
浏览器访问 GET /health
-> FastAPI 找到 health_check() 函数
-> 函数返回 Python 字典
-> FastAPI 自动转成 JSON
-> 浏览器收到 200 成功响应
```

## 我学到的路由、参数校验和依赖注入
路由
@app.post("/chat")
路由表示：当用户发送 POST /chat 请求时，FastAPI 执行对应的 chat() 函数。
参数校验
request: ChatRequest
FastAPI 会使用 Pydantic 校验用户发送的 JSON。
例如：
message 不能为空
temperature 必须在 0 到 2 之间
如果数据不符合规则，FastAPI 会直接返回 422，不会调用 DeepSeek。
依赖注入
client: LLMClient
settings: Annotated[Settings, Depends(get_settings)]
依赖注入表示 chat() 不需要自己读取 .env 或创建 DeepSeek Client。
FastAPI 会自动准备好配置和客户端，再传给 chat() 函数。
这样代码会更清晰，也方便后续复用、测试和替换模型服务。

你原来的理解已经抓住了“用户请求 -> 后端 -> 大模型 -> 返回结果”这个主线。现在主要是把 `health`、`chat`、路由和 JSON 这些词说得更准确。


