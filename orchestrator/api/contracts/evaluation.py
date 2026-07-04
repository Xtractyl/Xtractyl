from pydantic import BaseModel, Field


class EvaluateProjectsRequest(BaseModel):
    groundtruth_project: str = Field(..., min_length=1)
    comparison_project: str = Field(..., min_length=1)


class SaveAsGtSetRequest(BaseModel):
    source_project: str = Field(min_length=1)


class ProjectNamesResponse(BaseModel):
    names: list[str]


class EvaluateProjectsResponse(BaseModel):
    groundtruth_project: str
    groundtruth_project_id: int
    comparison_project: str
    comparison_project_id: int
    run_at_raw: str | None
    metrics: dict
    answer_comparison: list
    evaluation_output_path: str


class SaveAsGtSetResponse(BaseModel):
    status: str


class GroundtruthQalsResponse(BaseModel):
    sets: dict[str, dict]


class CompatibleGroundtruthSetsRequest(BaseModel):
    comparison_project: str = Field(..., min_length=1)


class CompatibleGroundtruthSetsResponse(BaseModel):
    names: list[str]
