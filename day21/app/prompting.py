from app.models import Message


SYSTEM_PROMPT = """
你是一个帮助用户学习 Agent 应用开发的助手。
你的回答要准确、简洁，优先解释工程实现。
如果用户的问题和之前的对话有关，你需要结合历史上下文回答。
""".strip()


def build_llm_messages(
    history_messages: list[Message],
    current_message: str,
    max_history_messages: int = 10,
) -> list[dict[str, str]]:
    """把数据库里的历史消息拼接成 LLM API 需要的 messages。"""

    llm_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    recent_history = history_messages[-max_history_messages:]

    for message in recent_history:
        if message.role not in {"user", "assistant"}:
            continue

        llm_messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    llm_messages.append(
        {
            "role": "user",
            "content": current_message,
        }
    )

    return llm_messages