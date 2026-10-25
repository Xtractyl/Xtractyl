# orchestrator/domain/models/evaluation.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class EvaluateProjectsCommand(BaseModel):
    groundtruth_project: str
    comparison_project: str

    @classmethod
    def from_contract(cls, groundtruth_project: str, comparison_project: str):
        try:
            return cls(
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


class ListGroundtruthProjectsForComparisonCommand(BaseModel):
    comparison_project: str

    @classmethod
    def from_contract(cls, comparison_project: str):
        return cls(comparison_project=comparison_project)
