# orchestrator/api/contracts/evaluation_views.py

from typing import Literal

from pydantic import BaseModel, Field

from api.contracts.evaluation import ComparisonEntry


class ProjectNameRequest(BaseModel):
    """Shared by Regression and Drift — both now take a single project
    name, replacing the earlier four-field configuration-filter request."""

    project_name: str = Field(..., min_length=1)


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
