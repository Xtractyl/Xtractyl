# orchestrator/domain/models/results.py

from api.contracts.results import GetResultsTableRequest
from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class GetResultsTableCommand(BaseModel):
    token: str
    project_name: str

    @classmethod
    def from_contract(cls, contract: GetResultsTableRequest, token: str):
        try:
            return cls(token=token, project_name=contract.project_name)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
