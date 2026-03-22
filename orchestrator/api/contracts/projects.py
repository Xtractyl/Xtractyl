# orchestrator/api/contracts/projects.py

from typing import Any

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=3)
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class ListQalJsonsRequest(BaseModel):
    project: str = Field(..., min_length=1)


class PreviewQalRequest(BaseModel):
    project: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)


class CreateProjectResponse(BaseModel):
    project_id: int


class ListHtmlSubfoldersResponse(BaseModel):
    subfolders: list[str]


class ListQalJsonsResponse(BaseModel):
    files: list[str]


class PreviewQalResponse(BaseModel):
    data: Any
