# orchestrator/domain/models/evaluation_drift.py

from pydantic import BaseModel


class GetEvaluationDriftCommand(BaseModel):
    @classmethod
    def from_contract(cls, data: dict):  # dictionary currently unused
        # we do not raise anything here because currently the domain does not need any input
        return cls()
