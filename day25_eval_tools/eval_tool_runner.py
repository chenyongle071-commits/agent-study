import json
import time
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


API_URL = "http://127.0.0.1:8000/agent/run"
BASE_DIR = Path(__file__).parent
QUESTION_FILE = BASE_DIR / "eval_tools.jsonl"
RESULT_FILE = BASE_DIR / "eval_tool_results.jsonl"


def load_questions() -> list[dict]:
    questions = []

    with QUESTION_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            questions.append(json.loads(line))

    return questions


def post_agent_run(payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib_request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=60) as response:
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


def get_actual_tool(response_body: dict) -> str | None:
    tool_result = response_body.get("tool_result")

    if not isinstance(tool_result, dict):
        return None

    return tool_result.get("selected_tool")


def get_actual_params(response_body: dict) -> dict | None:
    tool_result = response_body.get("tool_result")

    if not isinstance(tool_result, dict):
        return None

    selected_params = tool_result.get("selected_params")

    if isinstance(selected_params, dict):
        return selected_params

    return None


def normalize_value(value):
    if isinstance(value, list):
        return sorted(value)

    return value


def compare_params(expected_params: dict, actual_params: dict | None) -> bool:
    if actual_params is None:
        return False

    for key, expected_value in expected_params.items():
        actual_value = actual_params.get(key)

        if normalize_value(actual_value) != normalize_value(expected_value):
            return False

    return True


def judge_task_completed(status_code: int, response_body: dict) -> bool:
    if status_code >= 500 or status_code == 0:
        return False

    if response_body.get("route") == "blocked":
        return False

    if response_body.get("answer"):
        return True

    if response_body.get("tool_result"):
        return True

    if response_body.get("detail"):
        return True

    return False


def main() -> None:
    questions = load_questions()
    results = []

    tool_correct_count = 0
    params_correct_count = 0
    task_completed_count = 0

    for item in questions:
        payload = {
            "user_id": item["user_id"],
            "question": item["question"],
            "thread_id": "day25-tool-eval",
            "confirmed": True,
            "request_id": f"day25-{item['id']}",
        }

        start = time.perf_counter()
        status_code, response_body = post_agent_run(payload)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        actual_tool = get_actual_tool(response_body)
        actual_params = get_actual_params(response_body)

        tool_correct = actual_tool == item["expected_tool"]
        params_correct = compare_params(item["expected_params"], actual_params)
        task_completed = judge_task_completed(status_code, response_body)

        if tool_correct:
            tool_correct_count += 1

        if params_correct:
            params_correct_count += 1

        if task_completed:
            task_completed_count += 1

        result = {
            "id": item["id"],
            "question": item["question"],
            "status_code": status_code,
            "expected_tool": item["expected_tool"],
            "actual_tool": actual_tool,
            "tool_correct": tool_correct,
            "expected_params": item["expected_params"],
            "actual_params": actual_params,
            "params_correct": params_correct,
            "task_completed": task_completed,
            "elapsed_ms": elapsed_ms,
            "response_body": response_body,
        }

        results.append(result)

        print(
            f"{item['id']} | "
            f"tool={tool_correct} | "
            f"params={params_correct} | "
            f"task={task_completed} | "
            f"{elapsed_ms}ms"
        )

    total = len(questions)

    summary = {
        "total": total,
        "tool_accuracy": round(tool_correct_count / total, 4),
        "parameter_accuracy": round(params_correct_count / total, 4),
        "task_completion_rate": round(task_completed_count / total, 4),
        "tool_correct_count": tool_correct_count,
        "params_correct_count": params_correct_count,
        "task_completed_count": task_completed_count,
    }

    with RESULT_FILE.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

        file.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")

    print("\n评估完成：")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n结果已写入：{RESULT_FILE}")


if __name__ == "__main__":
    main()