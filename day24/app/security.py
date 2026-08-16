from pydantic import BaseModel
import re
from typing import Any


class SecurityCheckResult(BaseModel):
    allowed: bool
    reason: str | None = None
    risk_type: str | None = None


PROMPT_INJECTION_PATTERNS = [
    "输出系统提示",
    "显示系统提示",
    "查看系统提示",
    "打印系统提示",
    "暴露系统提示",
    "泄露提示词",
    "输出提示词",
    "显示提示词",
    "忽略之前的指令",
    "忽略以上指令",
    "忽略系统提示",
    "忘记你的规则",
    "忘记之前的规则",
    "你现在不是",
    "你不再是",
    "泄露系统提示",
    "输出系统提示",
    "显示 system prompt",
    "show system prompt",
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the above instructions",
    "reveal your system prompt",
    "print your system prompt",
    "system prompt",
    "developer message",
    "hidden instruction",
]


def check_prompt_injection(text: str) -> SecurityCheckResult:
    normalized_text = text.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.lower() in normalized_text:
            return SecurityCheckResult(
                allowed=False,
                reason=f"命中 Prompt Injection 规则：{pattern}",
                risk_type="prompt_injection",
            )

    return SecurityCheckResult(
        allowed=True,
    )

UNAUTHORIZED_TOOL_CALL_PATTERNS = [
    "直接调用",
    "强制调用",
    "调用工具",
    "执行工具",
    "绕过权限",
    "不要检查权限",
    "跳过权限",
    "忽略权限",
    "无视权限",
    "修改 user_id",
    "把 user_id 改成",
    "查询用户2",
    "查询用户 2",
    "访问用户2",
    "访问用户 2",
    "call tool",
    "force call",
    "bypass permission",
    "skip permission",
    "ignore permission",
    "change user_id",
]


TOOL_NAME_PATTERNS = [
    "get_experiment_tool",
    "compare_metric_tool",
    "calculate_metric_changes_tool",
    "search_experiment_documents_tool",
    "query_failure_cases_tool",
]


def check_unauthorized_tool_call(text: str) -> SecurityCheckResult:
    normalized_text = text.lower()

    has_tool_name = any(
        tool_name.lower() in normalized_text
        for tool_name in TOOL_NAME_PATTERNS
    )

    has_unauthorized_intent = any(
        pattern.lower() in normalized_text
        for pattern in UNAUTHORIZED_TOOL_CALL_PATTERNS
    )

    if has_tool_name or has_unauthorized_intent:
        return SecurityCheckResult(
            allowed=False,
            reason="检测到疑似越权工具调用或权限绕过意图。",
            risk_type="unauthorized_tool_call",
        )

    return SecurityCheckResult(
        allowed=True,
    )

ALLOWED_METRICS = {
    "accuracy",
    "f1",
    "latency_ms",
    "cost",
}


DANGEROUS_PARAMETER_PATTERNS = [
    "password",
    "api_key",
    "secret",
    "token",
    "drop",
    "delete",
    "truncate",
    "insert",
    "update",
    "select *",
    "sql",
]


def check_parameter_whitelist(text: str) -> SecurityCheckResult:
    normalized_text = text.lower()

    for pattern in DANGEROUS_PARAMETER_PATTERNS:
        if pattern in normalized_text:
            return SecurityCheckResult(
                allowed=False,
                reason=f"请求参数包含不允许的内容：{pattern}",
                risk_type="invalid_parameter",
            )

    return SecurityCheckResult(
        allowed=True,
    )

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "token",
    "secret",
    "password",
    "llm_api_key",
}


def mask_sensitive_text(text: str) -> str:
    masked_text = text

    patterns = [
        (r"sk-[A-Za-z0-9_-]{10,}", "sk-***"),
        (r"Bearer\s+[A-Za-z0-9._-]+", "Bearer ***"),
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "***@***.***"),
        (r"1[3-9]\d{9}", "1**********"),
    ]

    for pattern, replacement in patterns:
        masked_text = re.sub(pattern, replacement, masked_text)

    return masked_text


def sanitize_log_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return mask_sensitive_text(payload)

    if isinstance(payload, dict):
        safe_payload = {}

        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS:
                safe_payload[key] = "***"
            else:
                safe_payload[key] = sanitize_log_payload(value)

        return safe_payload

    if isinstance(payload, list):
        return [sanitize_log_payload(item) for item in payload]

    return payload

HIGH_RISK_ACTION_PATTERNS = [
    "删除",
    "清空",
    "重置",
    "覆盖",
    "批量删除",
    "删除实验",
    "修改实验",
    "delete",
    "remove",
    "reset",
    "drop",
    "truncate",
]


def check_high_risk_action(text: str) -> SecurityCheckResult:
    normalized_text = text.lower()

    for pattern in HIGH_RISK_ACTION_PATTERNS:
        if pattern.lower() in normalized_text:
            return SecurityCheckResult(
                allowed=False,
                reason=f"命中危险操作规则：{pattern}",
                risk_type="high_risk_action",
            )

    return SecurityCheckResult(allowed=True)