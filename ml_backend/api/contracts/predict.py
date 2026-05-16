# ml_backend/api/contracts/predict.py
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    ollama_model: str
    ollama_base: str
    system_prompt: str
    llm_timeout_seconds: int


class LabelStudioConfig(BaseModel):
    label_studio_url: str
    ls_token: str


class QuestionsAndLabels(BaseModel):
    questions: List[str] = Field(..., min_length=1)
    labels: List[str] = Field(..., min_length=1)


class PredictRequest(BaseModel):
    job_id: str
    task_id: str
    html: str = Field(..., min_length=1)
    questions_and_labels: QuestionsAndLabels
    llm_config: LLMConfig
    label_studio_config: LabelStudioConfig


class PredictResponse(BaseModel):
    model_version: str
    score: float
    result: List[Dict[str, Any]]
    meta: Dict[str, Any]
