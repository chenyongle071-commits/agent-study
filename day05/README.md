# Day05 Database 基础

## 今日目标

今天的目标是让 FastAPI 聊天服务具备数据库能力。

在 Day04 中，`/chat` 可以调用 DeepSeek 并返回回答，但不会保存历史记录。

Day05 的目标是：

```text
创建用户
-> 创建会话
-> 用户发送消息
-> 保存 user 消息
-> 调用 DeepSeek
-> 保存 assistant 消息
-> 查询会话历史
```

今日完成
创建 day05 项目，复制 day04 的 FastAPI 基础代码
安装 SQLModel
理解数据库基本概念
创建 User、Conversation、Message 三张表
创建数据库连接
实现创建用户接口：POST /users
实现创建会话接口：POST /conversations
修改 /chat：保存用户消息和模型回答
实现查看会话消息接口：GET /conversations/{conversation_id}/messages
准备 Git 提交
数据库基本概念
Database：数据库，比如 app.db
Table：表，比如 users、conversations、messages
Row：表里的一行数据
Column：字段，比如 id、email、content
Model：用 Python 类描述一张表
Engine：数据库连接入口
Session：一次数据库操作会话
commit：提交修改
select：查询数据
项目结构
Day05 是在 Day04 的 FastAPI 基础上继续开发的。
新增了两个关键文件：
app/models.py
app/database.py
其中：
models.py
定义数据库表模型，例如 User、Conversation、Message。

database.py
定义数据库连接、创建表函数、Session 依赖。

schemas.py
定义请求体和响应体，例如 UserCreate、UserRead、ConversationCreate、MessageRead。

main.py
定义 FastAPI 路由，并在接口中使用数据库。
依赖安装
进入 Day05 目录：
cd D:\agent_study\day05
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install sqlmodel
python -m pip freeze > requirements.txt
.env 配置从 Day04 复制到 Day05，用于读取 DeepSeek 的 API Key、Base URL 和模型名。
注意：
.env 不能上传 GitHub
app.db 也不建议上传 GitHub
三张表
users
保存用户信息。
主要字段：
id
email
created_at
conversations
保存会话信息。
主要字段：
id
user_id
title
created_at
messages
保存聊天消息。
主要字段：
id
conversation_id
role
content
created_at
三张表关系：
一个 user 可以有多个 conversations
一个 conversation 可以有多条 messages
接口流程
POST /users
创建用户。
流程：
Swagger 发 POST /users
-> FastAPI 接收 JSON
-> UserCreate 校验 email
-> 查询数据库是否已有该邮箱
-> 创建 User 对象
-> session.add()
-> session.commit()
-> session.refresh()
-> 返回 UserRead
POST /conversations
创建会话。
流程：
Swagger 发 POST /conversations
-> FastAPI 接收 JSON
-> ConversationCreate 校验 user_id 和 title
-> 查询 user_id 对应的用户是否存在
-> 创建 Conversation 对象
-> 写入数据库
-> 返回 ConversationRead
POST /chat
调用大模型并保存消息。
流程：
Swagger 发 POST /chat
-> FastAPI 接收 JSON
-> ChatRequest 校验 conversation_id、message、temperature
-> 查询 conversation_id 对应的会话是否存在
-> 保存 user 消息
-> 调用 DeepSeek
-> 保存 assistant 消息
-> 返回 ChatResponse
GET /conversations/{conversation_id}/messages
查询会话历史消息。
流程：
Swagger 发 GET /conversations/1/messages
-> FastAPI 读取路径参数 conversation_id
-> 查询会话是否存在
-> 查询该会话下的所有 messages
-> 按 created_at 排序
-> 返回消息列表

今日理解
今天我理解到，FastAPI 后端不只是接收请求和返回结果，还需要把业务数据保存下来。
SQLModel 可以用 Python 类描述数据库表。
FastAPI 可以通过依赖注入拿到数据库 Session。
Pydantic 负责请求和响应数据校验。
SQLModel/SQLAlchemy 负责把 Python 对象写入数据库。
当前 /chat 已经可以做到：
接收用户消息
-> 调用真实 DeepSeek API
-> 保存用户消息和模型回复
-> 查询历史记录
这为后续多轮会话、RAG、Agent Memory 和工具调用日志打下了基础。

另外，你最后那句可以这样理解更准确：

> 创建三张表，需要在 `models.py` 中定义三个数据库模型；同时在 `schemas.py` 中定义对应的请求和响应模型；最后在 `main.py` 中写路由接口来操作这些表。

这个表述就很工程化了。