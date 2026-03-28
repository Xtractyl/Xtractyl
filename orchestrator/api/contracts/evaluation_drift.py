# orchestrator/api/contracts/evaluation_drift.py

from typing import Optional

from pydantic import BaseModel, Field


class GetEvaluationDriftRequest(BaseModel):
    # Future-proof query params (all optional so current frontend GET works)
    set_name: Optional[str] = Field(default=None, min_length=1)
    # example for later extension:
    # window_days: Optional[int] = Field(default=None, ge=1)


class EvaluationDriftEntry(BaseModel):
    series: str
    run_at_raw: str | None
    groundtruth_project_id: int
    comparison_project_id: int
    model: str
    system_prompt: str | None = None
    questions: list[str] | None = None
    labels: list[str] | None = None
    metrics: dict


class EvaluationDriftSet(BaseModel):
    series: str
    entries: list[EvaluationDriftEntry]


class GetEvaluationDriftResponse(BaseModel):
    sets: list[EvaluationDriftSet]
