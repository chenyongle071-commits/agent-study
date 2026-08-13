from fastapi import HTTPException
from sqlmodel import Session

from app.models import Experiment
from app.tool_schemas import (
    CompareMetricInput,
    CompareMetricResult,
    ExperimentToolResult,
    GetExperimentInput,
)


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