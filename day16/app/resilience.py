from collections.abc import Callable
from time import monotonic
from typing import TypeVar

from fastapi import HTTPException, Request
from openai import OpenAI

T = TypeVar("T")


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._records: dict[str, list[float]] = {}

    def check(self, key: str) -> None:
        now = monotonic()
        window_start = now - self.window_seconds

        timestamps = self._records.get(key, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]

        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试。",
            )

        timestamps.append(now)
        self._records[key] = timestamps


rate_limiter = RateLimiter(max_requests=5, window_seconds=60)


def call_with_retry(
    func: Callable[[], T],
    retries: int = 2,
    sleep_seconds: float = 1.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            return func()
        except Exception as error:
            last_error = error
            if attempt < retries:
                import time

                time.sleep(sleep_seconds)

    assert last_error is not None
    raise last_error


def build_rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    return client_host