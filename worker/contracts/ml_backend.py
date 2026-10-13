# worker/contracts/ml_backend.py
from pydantic import BaseModel, Field

from contracts.jobs import QuestionsAndLabels


class LLMConfig(BaseModel):
    ollama_model: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)


class LabelStudioConfig(BaseModel):
    ls_token: str = Field(..., min_length=1)


class PredictRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    html: str = Field(..., min_length=1)
    questions_and_labels: QuestionsAndLabels
    llm_config: LLMConfig
    label_studio_config: LabelStudioConfig


class PredictMeta(BaseModel):
    predictions: list
    raw_llm_answers: dict
    dom_match_diagnostics: list
    dom_match_by_label: dict
    task_ms_total: float
    task_ms_llm_total: float
    task_ms_dom_extract: float
    task_ms_dom_match: float
    n_llm_calls: int
    avg_llm_call_ms: float
    median_llm_call_ms: float


class PredictResponse(BaseModel):
    model_version: str
    score: float
    result: list[dict]
    meta: PredictMeta


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str | None = None
    details: list | None = None
