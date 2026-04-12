# orchestrator/api/contracts/jobs.py

from pydantic import BaseModel, Field


class JobStatusRequest(BaseModel):
    job_id: str = Field(..., min_length=1)


class JobStatusResponse(BaseModel):
    job_id: str
    state: str
    progress: str | None = None
    project_name: str | None = None
    model: str | None = None
    created_at: str | None = None
    error: str | None = None
    result: dict | None = None
