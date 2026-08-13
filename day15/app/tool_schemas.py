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