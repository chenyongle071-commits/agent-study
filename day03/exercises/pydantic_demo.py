#定义 ChatMessage、ChatRequest 这种结构。
#自动校验 role、content、temperature 等字段。

#Pydantic 就是“把一堆原始数据，变成结构化、可校验的数据对象”。
#Pydantic 用来定义数据结构，并在数据进入系统时做校验。它能提前发现字段缺失、类型错误、取值范围错误、枚举值错误等问题。
#Pydantic 是一个第三方数据校验库。它利用 Python 类型标注来定义规则，并在创建模型或校验数据时执行这些规则。

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

#原始请求数据，可能乱、可能错、可能类型不对。
#Pydantic 可以把它变成结构化数据，并把错误提前拦住。

# ChatMessage 表示一条聊天消息。
# role 限制为 system、user、assistant 三种消息角色。
#这个类继承了 BaseModel，所以我要按照这些类型标注来做运行时校验。这也是pydantic区别于day02的类型标注的最关键点
#类型标注只是建议对应的值有对应的类型，但是oydantic要检查这个是否是对应的
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)

# ChatRequest 表示一次聊天请求的数据结构。
# 它规定了 user_id、model、temperature、messages 这些字段，并负责校验它们是否合法。
class ChatRequest(BaseModel):
    user_id: int
    model: str = "gpt-4.1-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    messages: list[ChatMessage]


if __name__ == "__main__":
    good_payload = {
        "user_id": "1",
        "model": "gpt-4.1-mini",
        "temperature": 0.5,
        "messages": [
            {"role": "user", "content": "帮我总结这个实验结果"},
            {"role": "assistant", "content": "当然可以。"},
        ],
    }

    request = ChatRequest.model_validate(good_payload)
    print("校验成功：")
    print(request) 
    print(request.model_dump())

    bad_payload = {
        "user_id": "abc",
        "model": "gpt-4.1-mini",
        "temperature": 3,
        "messages": [
            {"role": "robot", "content": ""},
        ],
    }

    try:
        ChatRequest.model_validate(bad_payload)
    except ValidationError as error:
        print("\n校验失败：")
        print(error)


