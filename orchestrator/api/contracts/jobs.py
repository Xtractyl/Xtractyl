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


class TaskPrelabellingMetaRequest(BaseModel):
    job_id: str
    task_id: int
    filename: str
    predictions: list
    raw_llm_answers: dict
    dom_match_diagnostics: list
    dom_match_by_label: dict
    task_ms_total: float
    task_ms_llm_total: float
    task_ms_dom_extract: float
    task_ms_dom_match: float
    n_llm_calls: int
    n_timeouts: int
    avg_llm_call_ms: float
    median_llm_call_ms: float


class TaskPrelabellingMetaResponse(BaseModel):
    status: str
