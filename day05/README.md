1. 创建 day05 项目，复制 day04 的 FastAPI 基础
2. 安装 SQLModel
3. 理解数据库基本概念
4. 创建 User、Conversation、Message 三张表
5. 创建数据库连接
6. 实现创建用户
7. 实现创建会话
8. 修改 /chat：保存用户消息和模型回答
9. 实现查看会话消息
10. Git 提交

Database：数据库，比如 app.db
Table：表，比如 users、conversations、messages
Row：表里的一行数据
Column：字段，比如 id、email、content
Model：用 Python 类描述一张表
Engine：数据库连接入口
Session：一次数据库操作会话
commit：提交修改
select：查询数据


将day04的FastAPI基础代码复制到day05，然后添加models和database文件
调用deepseek的.env代码也同样复制
cd D:\agent_study\day05
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install sqlmodel
python -m pip freeze > requirements.txt
创建虚拟环境并下载相关依赖和sqlmodel依赖

在加入新的post或get等请求，访问http://127.0.0.1:8000/docs页面，用来测试
Swagger 发 POST /users
-> FastAPI 接收 JSON
-> UserCreate 校验 email
-> 查询数据库是否已有该邮箱
-> 创建 User 对象
-> session.add()
-> session.commit()
-> session.refresh()
-> 返回 UserRead

创建三个表，就需要三个模块得对应接受和处理代码，然后在main文件中导入，测试
