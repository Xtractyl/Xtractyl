# orchestrator/api/contracts/evaluation_drift.py

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class GetEvaluationDriftRequest(BaseModel):
    # Future-proof query params (all optional so current frontend GET works)
    set_name: Optional[str] = Field(default=None, min_length=1)
    # example for later extension:
    # window_days: Optional[int] = Field(default=None, ge=1)


# Minimal response envelope for ok() wrapper (no concrete data contract yet)
class OkResponseAny(BaseModel):
    status: Literal["success"] = "success"
    data: Any
