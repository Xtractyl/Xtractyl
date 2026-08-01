# orchestrator/api/contracts/evaluation_views.py

from pydantic import BaseModel, Field

from api.contracts.evaluation import ComparisonEntry


class ProjectNameRequest(BaseModel):
    """Shared by Regression and Drift — both now take a single project
    name, replacing the earlier four-field configuration-filter request."""

    project_name: str = Field(..., min_length=1)


class GetRegressionViewResponse(BaseModel):
    groundtruth_project: str | None = None
    entries: list[ComparisonEntry]


class GetDriftViewResponse(BaseModel):
    entries: list[ComparisonEntry]
