# orchestrator/domain/models/evaluation.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


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
