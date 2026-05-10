# worker/contracts/jobs.py
from pydantic import BaseModel, Field


class QuestionsAndLabels(BaseModel):
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class JobPayload(BaseModel):
    job_id: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    questions_and_labels: QuestionsAndLabels
