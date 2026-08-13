import asyncio
from collections.abc import AsyncIterator

from openai import OpenAI


async def stream_deepseek_answer(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    full_text = ""

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue

        full_text += delta
        yield f"data: {delta}\n\n"

    yield f"event: done\ndata: [DONE]\n\n"