import json
import time
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


BASE_URL = "http://127.0.0.1:8000"
SEARCH_URL = f"{BASE_URL}/rag/search"
ANSWER_URL = f"{BASE_URL}/rag/answer"

BASE_DIR = Path(__file__).parent
QUESTION_FILE = BASE_DIR / "eval_rag_questions.jsonl"
RESULT_FILE = BASE_DIR / "eval_rag_results.jsonl"
FAILURE_FILE = BASE_DIR / "failure_cases.jsonl"


def load_questions() -> list[dict]:
    questions = []

    with QUESTION_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            questions.append(json.loads(line))

    return questions


def post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib_request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=120) as response:
            response_data = response.read().decode("utf-8")
            return response.status, json.loads(response_data)
    except HTTPError as error:
        error_data = error.read().decode("utf-8")
        try:
            body = json.loads(error_data)
        except json.JSONDecodeError:
            body = {"detail": error_data}

        return error.code, body
    except URLError as error:
        return 0, {"detail": f"请求失败：{error}"}


def text_contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()

    return any(
        keyword.lower() in text_lower
        for keyword in keywords
    )


def text_contains_all(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()

    return all(
        keyword.lower() in text_lower
        for keyword in keywords
    )


def estimate_tokens(text: str) -> int:
    chinese_chars = 0
    other_chars = 0

    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            chinese_chars += 1
        elif not char.isspace():
            other_chars += 1

    return chinese_chars + max(1, other_chars // 4)


def build_search_payload(item: dict) -> dict:
    return {
        "user_id": item["user_id"],
        "query": item["query"],
        "top_k": item["top_k"],
    }


def build_answer_payload(item: dict) -> dict:
    return {
        "user_id": item["user_id"],
        "query": item["query"],
        "top_k": item["top_k"],
        "temperature": 0.2,
    }


def extract_search_text(search_body: dict) -> str:
    results = search_body.get("results", [])

    if not isinstance(results, list):
        return ""

    texts = []

    for result in results:
        if isinstance(result, dict):
            texts.append(str(result.get("text", "")))

    return "\n".join(texts)


def extract_answer_text(answer_body: dict) -> str:
    return str(answer_body.get("answer", ""))


def extract_source_text(answer_body: dict) -> str:
    sources = answer_body.get("sources", [])

    if not isinstance(sources, list):
        return ""

    texts = []

    for source in sources:
        if isinstance(source, dict):
            texts.append(str(source.get("text", "")))
            texts.append(str(source.get("filename", "")))

    return "\n".join(texts)


def evaluate_one(item: dict) -> dict:
    search_payload = build_search_payload(item)
    answer_payload = build_answer_payload(item)

    search_start = time.perf_counter()
    search_status, search_body = post_json(SEARCH_URL, search_payload)
    search_elapsed_ms = round((time.perf_counter() - search_start) * 1000, 2)

    answer_start = time.perf_counter()
    answer_status, answer_body = post_json(ANSWER_URL, answer_payload)
    answer_elapsed_ms = round((time.perf_counter() - answer_start) * 1000, 2)

    search_text = extract_search_text(search_body)
    answer_text = extract_answer_text(answer_body)
    source_text = extract_source_text(answer_body)

    recall_hit = (
        search_status == 200
        and text_contains_any(search_text, item["expected_source_keywords"])
    )

    answer_keyword_hit = (
        answer_status == 200
        and text_contains_all(answer_text, item["expected_answer_keywords"])
    )

    source_keyword_hit = (
        answer_status == 200
        and text_contains_any(source_text, item["expected_source_keywords"])
    )

    answer_supported = answer_keyword_hit and source_keyword_hit

    input_tokens = estimate_tokens(item["query"])
    context_tokens = estimate_tokens(search_text)
    answer_tokens = estimate_tokens(answer_text)
    total_estimated_tokens = input_tokens + context_tokens + answer_tokens

    success = recall_hit and answer_keyword_hit and source_keyword_hit

    return {
        "id": item["id"],
        "query": item["query"],
        "search_status": search_status,
        "answer_status": answer_status,
        "recall_hit": recall_hit,
        "answer_keyword_hit": answer_keyword_hit,
        "source_keyword_hit": source_keyword_hit,
        "answer_supported": answer_supported,
        "success": success,
        "search_elapsed_ms": search_elapsed_ms,
        "answer_elapsed_ms": answer_elapsed_ms,
        "total_elapsed_ms": round(search_elapsed_ms + answer_elapsed_ms, 2),
        "estimated_tokens": {
            "input_tokens": input_tokens,
            "context_tokens": context_tokens,
            "answer_tokens": answer_tokens,
            "total": total_estimated_tokens,
        },
        "expected_answer_keywords": item["expected_answer_keywords"],
        "expected_source_keywords": item["expected_source_keywords"],
        "search_body": search_body,
        "answer_body": answer_body,
    }


def summarize(results: list[dict]) -> dict:
    total = len(results)

    recall_count = sum(1 for item in results if item["recall_hit"])
    answer_keyword_count = sum(1 for item in results if item["answer_keyword_hit"])
    source_keyword_count = sum(1 for item in results if item["source_keyword_hit"])
    supported_count = sum(1 for item in results if item["answer_supported"])
    success_count = sum(1 for item in results if item["success"])

    avg_latency = round(
        sum(item["total_elapsed_ms"] for item in results) / total,
        2,
    )

    avg_tokens = round(
        sum(item["estimated_tokens"]["total"] for item in results) / total,
        2,
    )

    return {
        "total": total,
        "recall_at_k": round(recall_count / total, 4),
        "answer_keyword_hit_rate": round(answer_keyword_count / total, 4),
        "source_keyword_hit_rate": round(source_keyword_count / total, 4),
        "answer_supported_rate": round(supported_count / total, 4),
        "success_rate": round(success_count / total, 4),
        "failure_count": total - success_count,
        "avg_latency_ms": avg_latency,
        "avg_estimated_tokens": avg_tokens,
    }


def main() -> None:
    questions = load_questions()
    results = []

    for item in questions:
        result = evaluate_one(item)
        results.append(result)

        print(
            f"{item['id']} | "
            f"recall={result['recall_hit']} | "
            f"answer={result['answer_keyword_hit']} | "
            f"source={result['source_keyword_hit']} | "
            f"success={result['success']} | "
            f"{result['total_elapsed_ms']}ms"
        )

    summary = summarize(results)
    failures = [
        result
        for result in results
        if not result["success"]
    ]

    with RESULT_FILE.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

        file.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")

    with FAILURE_FILE.open("w", encoding="utf-8") as file:
        for failure in failures:
            file.write(json.dumps(failure, ensure_ascii=False) + "\n")

    print("\n评估完成：")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n结果已写入：{RESULT_FILE}")
    print(f"失败案例已写入：{FAILURE_FILE}")


if __name__ == "__main__":
    main()