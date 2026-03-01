# orchestrator/api/contracts/results.py

from typing import Any, Literal

from pydantic import BaseModel, Field


class GetResultsTableRequest(BaseModel):
    project_name: str = Field(..., min_length=1)


# Minimal response envelope for ok() wrapper (no concrete data contract yet)
class OkResponseAny(BaseModel):
    status: Literal["success"] = "success"
    data: Any
