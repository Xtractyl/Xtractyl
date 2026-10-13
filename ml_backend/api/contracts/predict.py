# ml_backend/api/contracts/predict.py
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    ollama_model: str
    system_prompt: str


class LabelStudioConfig(BaseModel):
    ls_token: str


class QuestionsAndLabels(BaseModel):
    questions: List[str] = Field(..., min_length=1)
    labels: List[str] = Field(..., min_length=1)


class PredictRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    html: str = Field(..., min_length=1)
    questions_and_labels: QuestionsAndLabels
    llm_config: LLMConfig
    label_studio_config: LabelStudioConfig


class PredictMeta(BaseModel):
    predictions: List[Dict[str, Any]]
    raw_llm_answers: Dict[str, Any]
    dom_match_diagnostics: List[Dict[str, Any]]
    dom_match_by_label: Dict[str, Optional[bool]]
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
    result: List[Dict[str, Any]]
    meta: PredictMeta
