# worker/contracts/orchestrator.py
from pydantic import BaseModel, ConfigDict, Field, model_validator

from contracts.ml_backend import PredictMeta


class TaskResultRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    task_id: int
    filename: str = Field(..., min_length=1)
    success: bool
    error: str | None
    result: PredictMeta | None

    @model_validator(mode="after")
    def _success_matches_content(self) -> "TaskResultRequest":
        if self.success and (self.result is None or self.error is not None):
            raise ValueError("a successful task needs a result and no error")
        if not self.success and (self.error is None or self.result is not None):
            raise ValueError("a failed task needs an error and no result")
        return self


class TaskResultResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    continue_: bool = Field(alias="continue")
