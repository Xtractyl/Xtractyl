# orchestrator/api/contracts/evaluation.py

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluateProjectsRequest(BaseModel):
    groundtruth_project: str = Field(..., min_length=1)
    comparison_project: str = Field(..., min_length=1)


# Minimal response envelope for ok() wrapper (no concrete data contract yet)
class OkResponseAny(BaseModel):
    status: Literal["success"] = "success"
    data: Any
