from typing import Literal

from pydantic import BaseModel, Field


class GetExperimentInput(BaseModel):
    user_id: int = Field(ge=1)
    experiment_id: int = Field(ge=1)


class CompareMetricInput(BaseModel):
    user_id: int = Field(ge=1)
    experiment_a_id: int = Field(ge=1)
    experiment_b_id: int = Field(ge=1)
    metric_name: Literal["accuracy", "f1", "latency_ms", "cost"]


class ExperimentToolResult(BaseModel):
    id: int
    user_id: int
    name: str
    model_name: str
    dataset_name: str
    accuracy: float
    f1: float
    latency_ms: float
    cost: float
    status: str


class CompareMetricResult(BaseModel):
    experiment_a_id: int
    experiment_b_id: int
    metric_name: str
    a_value: float
    b_value: float
    delta: float
    better_experiment_id: int | None


class CalculateMetricChangesInput(BaseModel):
    user_id: int = Field(ge=1)
    experiment_a_id: int = Field(ge=1)
    experiment_b_id: int = Field(ge=1)
    metrics: list[Literal["accuracy", "f1", "latency_ms", "cost"]] = Field(min_length=1, max_length=4)


class MetricChangeItem(BaseModel):
    metric_name: str
    a_value: float
    b_value: float
    delta: float
    change_percent: float | None
    better_experiment_id: int | None


class CalculateMetricChangesResult(BaseModel):
    experiment_a_id: int
    experiment_b_id: int
    changes: list[MetricChangeItem]

class SearchExperimentDocumentsInput(BaseModel):
    user_id: int = Field(ge=1)
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchExperimentDocumentItem(BaseModel):
    chunk_id: str
    filename: str
    text: str
    retrieval_method: str
    distance: float


class SearchExperimentDocumentsResult(BaseModel):
    query: str
    results: list[SearchExperimentDocumentItem]


class QueryFailureCasesInput(BaseModel):
    user_id: int = Field(ge=1)
    category: Literal[
        "all",
        "direct_answer",
        "paraphrase",
        "keyword",
        "unknown",
        "irrelevant",
        "user_isolation",
        "document_update",
        "citation",
    ] = "all"
    only_failed: bool = True
    limit: int = Field(default=10, ge=1, le=50)


class FailureCaseItem(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    status_code: int
    passed: bool
    reasons: list[str]


class QueryFailureCasesResult(BaseModel):
    user_id: int
    category: str
    count: int
    cases: list[FailureCaseItem]
