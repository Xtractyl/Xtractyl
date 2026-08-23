# orchestrator/domain/models/results.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class GetResultsTableCommand(BaseModel):
    project_name: str

    @classmethod
    def from_contract(cls, project_name: str):
        try:
            return cls(project_name=project_name)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
