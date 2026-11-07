# orchestrator/api/contracts/projects.py

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=3)
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class ProjectLinksRequest(BaseModel):
    title: str = Field(..., min_length=3)
    questions: list[str] = Field(..., min_length=1)
    labels: list[str] = Field(..., min_length=1)


class DiscardProjectRequest(BaseModel):
    project: str = Field(..., min_length=3)


class UploadTasksRequest(BaseModel):
    project: str = Field(..., min_length=3)


class ProjectExistsRequest(BaseModel):
    project: str = Field(..., min_length=3)


class CreateProjectResponse(BaseModel):
    project_id: int


class ProjectLinksResponse(BaseModel):
    comparison: list[str]
    regression: list[str]
    drift: list[str]


class DiscardProjectResponse(BaseModel):
    status: str


class ListProjectsReadyForUploadResponse(BaseModel):
    projects: list[str]


class ListProjectsReadyForCreationResponse(BaseModel):
    projects: list[str]


class ListProjectsReadyForPrelabellingResponse(BaseModel):
    projects: list[str]


class ProjectExistsResponse(BaseModel):
    exists: bool


class UploadTasksResponse(BaseModel):
    status: str
