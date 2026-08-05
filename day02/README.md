# Day02 Python 工程基础

## 今日目标

- 创建 Python 虚拟环境
- 学习 Python 类型标注
- 学习异常处理
- 学习装饰器
- 完成 3 个小练习
- 提交 Git 记录

## 1. Python 虚拟环境

虚拟环境用于给当前项目创建独立的 Python 运行环境。

这样每个项目可以有自己的依赖，不会互相影响。

常用命令：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1

类型标注像是
异常处理的话就是在用户输入某些不符合规范的信息时，能做出一些判断，让这个违规消息有提示错误