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
    model: str | None = None
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


class ComparisonEntry(BaseModel):
    """Shared shape for a single evaluation row, reused by the Regression
    and Drift contracts in api/contracts/evaluation_views.py."""

    groundtruth_project: str
    comparison_prelabelling_run_id: int
    comparison_project: str | None = None
    model: str | None = None
    run_at_raw: str | None = None
    metrics: dict


class GetComparisonViewRequest(BaseModel):
    project_name: str = Field(..., min_length=1)


class GetComparisonViewResponse(BaseModel):
    entries: list[ComparisonEntry]


class ListEvaluatedProjectsResponse(BaseModel):
    projects: list[str]
