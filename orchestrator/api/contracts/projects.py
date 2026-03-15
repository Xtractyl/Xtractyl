# orchestrator/api/contracts/projects.py

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=3)
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class CreateProjectResponse(BaseModel):
    project_id: int
