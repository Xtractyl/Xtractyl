# orchestrator/domain/models/evaluation.py

from pydantic import BaseModel, Field, ValidationError

from domain.errors import ValidationFailed


class ProjectNameCommand(BaseModel):
    """Shared by Comparison, Regression and Drift — all three now accept
    ANY project with a resolvable evaluation family, not specifically the
    groundtruth project's own name (see resolve_family_for_project)."""

    project_name: str = Field(..., min_length=1)

    @classmethod
    def from_contract(cls, project_name: str) -> "ProjectNameCommand":
        try:
            return cls(project_name=project_name)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class EvaluateProjectsCommand(BaseModel):
    token: str
    groundtruth_project: str
    comparison_project: str

    @classmethod
    def from_contract(cls, groundtruth_project: str, comparison_project: str, token: str):
        try:
            return cls(
                token=token,
                groundtruth_project=groundtruth_project,
                comparison_project=comparison_project,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class SaveAsGtSetCommand(BaseModel):
    source_project: str
    token: str
    scope: str

    @classmethod
    def from_contract(cls, source_project: str, token: str, scope: str) -> "SaveAsGtSetCommand":
        return cls(source_project=source_project, token=token, scope=scope)


class CompatibleGroundtruthSetsCommand(BaseModel):
    comparison_project: str

    @classmethod
    def from_contract(cls, comparison_project: str):
        return cls(comparison_project=comparison_project)
