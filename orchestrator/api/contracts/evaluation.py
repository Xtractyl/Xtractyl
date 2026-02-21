# orchestrator/api/contracts/evaluation.py

from pydantic import BaseModel, Field


class EvaluateProjectsRequest(BaseModel):
    groundtruth_project: str = Field(..., min_length=1)
    comparison_project: str = Field(..., min_length=1)
