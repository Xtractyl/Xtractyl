# orchestrator/domain/models/projects.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class CreateProjectCommand(BaseModel):
    token: str
    title: str
    questions: list[str]
    labels: list[str]

    @classmethod
    def from_contract(cls, title: str, questions: list, labels: list, token: str):
        try:
            return cls(token=token, title=title, questions=questions, labels=labels)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
