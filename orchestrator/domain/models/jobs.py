# orchestrator/domain/models/jobs.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class PLACEHOLDERCommand(BaseModel):
    token: str
    project_name: str

    @classmethod
    def from_contract(cls, project_name: str, token: str):
        try:
            return cls(token=token, project_name=project_name)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
