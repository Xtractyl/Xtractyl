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


class QuestionsAndLabels(BaseModel):
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class EnqueueJobRequest(BaseModel):
    project_name: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    qal_file: str = Field(..., min_length=1)
    questions_and_labels: QuestionsAndLabels


class EnqueueJobResponse(BaseModel):
    job_id: str
    status_url: str
    cancel_url: str


class CancelJobResponse(BaseModel):
    job_id: str
    status: str


class PrelabelCallbackRequest(BaseModel):
    job_id: str
    status: str
    error: str | None = None


class PrelabelCallbackResponse(BaseModel):
    status: str
