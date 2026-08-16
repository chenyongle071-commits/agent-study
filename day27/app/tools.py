from fastapi import HTTPException
from sqlmodel import Session
import json
from pathlib import Path

from app.models import Experiment
from app.tool_schemas import (
    CalculateMetricChangesInput,
    CalculateMetricChangesResult,
    CompareMetricInput,
    CompareMetricResult,
    ExperimentToolResult,
    GetExperimentInput,
    MetricChangeItem,
    SearchExperimentDocumentsInput,
    SearchExperimentDocumentsResult,
    SearchExperimentDocumentItem,
    FailureCaseItem,
    QueryFailureCasesInput,
    QueryFailureCasesResult,
)
from app.retriever import hybrid_retrieve_chunks

FAILURE_CASES_FILE = Path(__file__).resolve().parents[2] / "day13_14" / "eval_results.jsonl"

def get_experiment_tool(
    params: GetExperimentInput,
    session: Session,
) -> ExperimentToolResult:
    """
    查询指定实验。

    工具必须检查 user_id，不能让用户访问别人的实验。
    """
    experiment = session.get(Experiment, params.experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="实验不存在。",
        )

    if experiment.user_id != params.user_id:
        raise HTTPException(
            status_code=403,
            detail="无权访问该实验。",
        )

    return ExperimentToolResult(
        id=experiment.id,
        user_id=experiment.user_id,
        name=experiment.name,
        model_name=experiment.model_name,
        dataset_name=experiment.dataset_name,
        accuracy=experiment.accuracy,
        f1=experiment.f1,
        latency_ms=experiment.latency_ms,
        cost=experiment.cost,
        status=experiment.status,
    )


def compare_metric_tool(
    params: CompareMetricInput,
    session: Session,
) -> CompareMetricResult:
    """
    对比两个实验的指定指标。
    """
    experiment_a = get_experiment_tool(
        params=GetExperimentInput(
            user_id=params.user_id,
            experiment_id=params.experiment_a_id,
        ),
        session=session,
    )

    experiment_b = get_experiment_tool(
        params=GetExperimentInput(
            user_id=params.user_id,
            experiment_id=params.experiment_b_id,
        ),
        session=session,
    )

    a_value = getattr(experiment_a, params.metric_name)
    b_value = getattr(experiment_b, params.metric_name)
    delta = b_value - a_value

    if params.metric_name in ("accuracy", "f1"):
        if b_value > a_value:
            better_experiment_id = experiment_b.id
        elif a_value > b_value:
            better_experiment_id = experiment_a.id
        else:
            better_experiment_id = None
    else:
        if b_value < a_value:
            better_experiment_id = experiment_b.id
        elif a_value < b_value:
            better_experiment_id = experiment_a.id
        else:
            better_experiment_id = None

    return CompareMetricResult(
        experiment_a_id=experiment_a.id,
        experiment_b_id=experiment_b.id,
        metric_name=params.metric_name,
        a_value=a_value,
        b_value=b_value,
        delta=delta,
        better_experiment_id=better_experiment_id,
    )

def calculate_metric_changes_tool(
    params: CalculateMetricChangesInput,
    session: Session,
) -> CalculateMetricChangesResult:
    """
    一次计算多个指标的变化。
    """
    changes = []

    for metric_name in params.metrics:
        compare_result = compare_metric_tool(
            params=CompareMetricInput(
                user_id=params.user_id,
                experiment_a_id=params.experiment_a_id,
                experiment_b_id=params.experiment_b_id,
                metric_name=metric_name,
            ),
            session=session,
        )

        if compare_result.a_value == 0:
            change_percent = None
        else:
            change_percent = (
                compare_result.delta / compare_result.a_value
            ) * 100

        changes.append(
            MetricChangeItem(
                metric_name=metric_name,
                a_value=compare_result.a_value,
                b_value=compare_result.b_value,
                delta=compare_result.delta,
                change_percent=change_percent,
                better_experiment_id=compare_result.better_experiment_id,
            )
        )

    return CalculateMetricChangesResult(
        experiment_a_id=params.experiment_a_id,
        experiment_b_id=params.experiment_b_id,
        changes=changes,
    )

def search_experiment_documents_tool(
    params: SearchExperimentDocumentsInput,
    session: Session,
) -> SearchExperimentDocumentsResult:
    chunks = hybrid_retrieve_chunks(
        query=params.query,
        user_id=params.user_id,
        session=session,
        top_k=params.top_k,
    )

    return SearchExperimentDocumentsResult(
        query=params.query,
        results=[
            SearchExperimentDocumentItem(
                chunk_id=chunk["id"],
                filename=chunk["metadata"].get("filename", "unknown"),
                text=chunk["text"],
                retrieval_method=chunk.get("retrieval_method", "vector"),
                distance=chunk["distance"],
            )
            for chunk in chunks
        ],
    )

def query_failure_cases_tool(
    params: QueryFailureCasesInput,
) -> QueryFailureCasesResult:
    if not FAILURE_CASES_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="未找到评测结果文件。",
        )

    rows = []
    with FAILURE_CASES_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    filtered_rows = [
        row for row in rows
        if row.get("user_id") == params.user_id
    ]

    if params.category != "all":
        filtered_rows = [
            row for row in filtered_rows
            if row.get("category") == params.category
        ]

    if params.only_failed:
        filtered_rows = [
            row for row in filtered_rows
            if not row.get("passed", False)
        ]

    def build_reasons(row: dict) -> list[str]:
        reasons = []
        if not row.get("answer_correct", False):
            reasons.append("answer_incorrect")
        if not row.get("source_filename_correct", True):
            reasons.append("source_filename_mismatch")
        if not row.get("source_content_correct", True):
            reasons.append("source_content_mismatch")
        if not row.get("recall_at_k", False):
            reasons.append("recall_failed")
        if row.get("status_code") not in (200, 404):
            reasons.append("unexpected_status")
        return reasons

    cases = [
        FailureCaseItem(
            id=row["id"],
            category=row["category"],
            question=row["question"],
            answer=row.get("answer", ""),
            status_code=row.get("status_code", 0),
            passed=row.get("passed", False),
            reasons=build_reasons(row),
        )
        for row in filtered_rows[:params.limit]
    ]

    return QueryFailureCasesResult(
        user_id=params.user_id,
        category=params.category,
        count=len(cases),
        cases=cases,
    )