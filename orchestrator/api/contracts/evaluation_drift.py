# orchestrator/api/contracts/evaluation_drift.py

from typing import Optional

from pydantic import BaseModel, Field


class GetEvaluationDriftRequest(BaseModel):
    # Future-proof query params (all optional so current frontend GET works)
    set_name: Optional[str] = Field(default=None, min_length=1)
    # example for later extension:
    # window_days: Optional[int] = Field(default=None, ge=1)


class EvaluationDriftEntry(BaseModel):
    ts: str
    series: str
    run_at_raw: str | None
    groundtruth_project_id: int
    comparison_project_id: int
    model: str
    qal_hash: str
    prompt_hash: str
    schema_hash: str
    metrics: dict


class GetEvaluationDriftResponse(BaseModel):
    series: str
    entries: list[EvaluationDriftEntry]
