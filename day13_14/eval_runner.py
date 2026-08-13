import json
import time
from pathlib import Path
from typing import Any

import httpx


BASE_URL = "http://127.0.0.1:8000"
QUESTION_FILE = Path("eval_questions.jsonl")
RESULT_FILE = Path("eval_results.jsonl")


def load_questions() -> list[dict[str, Any]]:
    questions = []

    with QUESTION_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            questions.append(json.loads(line))

    return questions


def call_rag_answer(question: dict[str, Any]) -> tuple[int, dict[str, Any], float]:
    payload = {
        "user_id": question["user_id"],
        "query": question["question"],
        "top_k": question.get("top_k", 3),
        "temperature": 0.3,
    }

    start_time = time.perf_counter()

    response = httpx.post(
        f"{BASE_URL}/rag/answer",
        json=payload,
        timeout=60,
    )

    elapsed_seconds = time.perf_counter() - start_time

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        response_json = {
            "raw_text": response.text,
        }

    return response.status_code, response_json, elapsed_seconds


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def evaluate_one(question: dict[str, Any], status_code: int, response_json: dict[str, Any], elapsed_seconds: float) -> dict[str, Any]:
    should_answer = question["should_answer"]
    expected_keywords = question.get("expected_answer_keywords") or []
    expected_source_filename = question.get("expected_source_filename")
    expected_source_contains = question.get("expected_source_contains")

    answer = response_json.get("answer", "")
    sources = response_json.get("sources", [])

    if status_code == 404:
        answer = response_json.get("detail", answer)

    answer_correct = contains_any(answer, expected_keywords)

    if should_answer:
        request_success = status_code == 200
    else:
        request_success = status_code in (200, 404)

    if expected_source_filename is None:
        source_filename_correct = True
    else:
        source_filename_correct = any(
            source.get("filename") == expected_source_filename
            for source in sources
        )

    if expected_source_contains is None:
        source_content_correct = True
    else:
        source_content_correct = any(
            expected_source_contains in source.get("text", "")
            for source in sources
        )

    recall_at_k = source_content_correct

    passed = (
        request_success
        and answer_correct
        and source_filename_correct
        and source_content_correct
    )

    return {
        "id": question["id"],
        "category": question["category"],
        "user_id": question["user_id"],
        "question": question["question"],
        "should_answer": should_answer,
        "status_code": status_code,
        "answer": answer,
        "sources": sources,
        "answer_correct": answer_correct,
        "source_filename_correct": source_filename_correct,
        "source_content_correct": source_content_correct,
        "recall_at_k": recall_at_k,
        "latency_seconds": round(elapsed_seconds, 3),
        "token_usage": response_json.get("usage"),
        "passed": passed,
    }


def print_summary(results: list[dict[str, Any]]) -> None:
    total = len(results)
    passed_count = sum(1 for result in results if result["passed"])
    recall_count = sum(1 for result in results if result["recall_at_k"])
    answer_correct_count = sum(1 for result in results if result["answer_correct"])
    source_correct_count = sum(1 for result in results if result["source_content_correct"])

    avg_latency = sum(result["latency_seconds"] for result in results) / total

    print("评测完成")
    print(f"总问题数：{total}")
    print(f"通过数：{passed_count}")
    print(f"通过率：{passed_count / total:.2%}")
    print(f"Recall@K：{recall_count / total:.2%}")
    print(f"回答正确率：{answer_correct_count / total:.2%}")
    print(f"引用内容正确率：{source_correct_count / total:.2%}")
    print(f"平均响应时间：{avg_latency:.3f}s")


def main() -> None:
    questions = load_questions()
    results = []

    with RESULT_FILE.open("w", encoding="utf-8") as file:
        for question in questions:
            status_code, response_json, elapsed_seconds = call_rag_answer(question)
            result = evaluate_one(
                question=question,
                status_code=status_code,
                response_json=response_json,
                elapsed_seconds=elapsed_seconds,
            )

            results.append(result)

            file.write(json.dumps(result, ensure_ascii=False) + "\n")

            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status} {result['id']} {result['category']} {result['latency_seconds']}s")

    print_summary(results)


if __name__ == "__main__":
    main()