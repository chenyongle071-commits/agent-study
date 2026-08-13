import json
from collections.abc import Sequence

from pydantic import BaseModel, Field


class StructuredAnswer(BaseModel):
    answer: str = Field(description="模型回答")
    confidence: float = Field(ge=0, le=1, description="置信度")


def build_json_prompt(question: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是一个帮助用户学习 Agent 应用开发的助手。"
                "请严格只输出 JSON，不要输出多余文字。"
                "JSON 必须包含 answer 和 confidence 两个字段。"
                "confidence 是 0 到 1 之间的小数。"
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]


def parse_structured_answer(raw_text: str) -> StructuredAnswer:
    data = json.loads(raw_text)
    return StructuredAnswer.model_validate(data)