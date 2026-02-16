# orchestrator/domain/models/evaluation_drift.py

from api.contracts.evaluation_drift import GetEvaluationDriftRequest
from pydantic import BaseModel


class GetEvaluationDriftCommand(BaseModel):
    @classmethod
    def from_contract(cls, contract: GetEvaluationDriftRequest):
        return cls()
