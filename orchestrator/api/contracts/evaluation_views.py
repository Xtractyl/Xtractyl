# orchestrator/api/contracts/evaluation_views.py

from typing import Literal

from pydantic import BaseModel, Field


class ProjectNameRequest(BaseModel):
    """Shared by Regression and Drift — both now take a single project
    name, replacing the earlier four-field configuration-filter request."""

    project_name: str = Field(..., min_length=3)


class ComparisonEntry(BaseModel):
    """Shared shape for a single evaluation row, reused by the Regression
    and Drift contracts in api/contracts/evaluation_views.py."""

    groundtruth_project: str
    comparison_prelabelling_run_id: int
    comparison_project: str
    model: str
    run_at_raw: str
    metrics: dict


class GetComparisonViewRequest(BaseModel):
    project_name: str = Field(..., min_length=3)
    scope: Literal["internal", "external"] = "external"


class GetComparisonViewResponse(BaseModel):
    entries: list[ComparisonEntry]


class RegressionViewRequest(ProjectNameRequest):
    """Regression-specific: scope filter, since external and internal
    groundtruth sets need different underlying queries (see
    get_regression_view)."""

    scope: Literal["internal", "external"] = "external"


class DriftViewRequest(ProjectNameRequest):
    """Drift-specific: scope filter, structurally identical to
    RegressionViewRequest, kept separate for clarity since the two views
    serve different purposes."""

    scope: Literal["internal", "external"] = "external"


class GetRegressionViewResponse(BaseModel):
    entries: list[ComparisonEntry]


class GetDriftViewResponse(BaseModel):
    entries: list[ComparisonEntry]
