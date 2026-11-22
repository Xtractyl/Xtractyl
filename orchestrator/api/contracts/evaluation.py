from typing import Literal

from pydantic import BaseModel, Field


class EvaluateProjectsRequest(BaseModel):
    groundtruth_project: str = Field(..., min_length=3)
    comparison_project: str = Field(..., min_length=3)


class SaveAsGtSetRequest(BaseModel):
    source_project: str = Field(min_length=3)
    scope: Literal["internal", "external"]


class ListProjectsReadyForComparisonResponse(BaseModel):
    projects: list[str]


class ListProjectsReadyForGroundtruthResponse(BaseModel):
    projects: list[str]


class EvaluateProjectsResponse(BaseModel):
    groundtruth_project: str
    groundtruth_project_id: int
    comparison_project: str
    comparison_project_id: int
    model: str
    run_at_raw: str
    metrics: dict


class SaveAsGtSetResponse(BaseModel):
    status: str


class GroundtruthQalsResponse(BaseModel):
    sets: dict[str, dict]


class ListGroundtruthProjectsForComparisonRequest(BaseModel):
    comparison_project: str = Field(..., min_length=3)


class ListGroundtruthProjectsForComparisonResponse(BaseModel):
    projects: list[str]


class ListEvaluatedProjectsResponse(BaseModel):
    projects: list[str]
