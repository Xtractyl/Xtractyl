# orchestrator/domain/models/ollama.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class ListModelsCommand(BaseModel):
    pass  # no input needed

    @classmethod
    def from_contract(cls):
        return cls()


class PullModelCommand(BaseModel):
    model: str

    @classmethod
    def from_contract(cls, model: str):
        try:
            return cls(model=model)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
