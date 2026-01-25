# orchestrator/domain/models/results.py

from api.contracts.results import GetResultsTableRequest
from pydantic import BaseModel


class GetResultsTableCommand(BaseModel):
    token: str
    project_name: str

    @classmethod
    def from_contract(cls, contract: GetResultsTableRequest, token: str):
        return cls(token=token, project_name=contract.project_name)
