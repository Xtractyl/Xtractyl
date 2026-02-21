# orchestrator/domain/models/evaluation.py

from api.contracts.evaluation import EvaluateProjectsRequest
from pydantic import BaseModel


class EvaluateProjectsCommand(BaseModel):
    token: str
    groundtruth_project: str
    comparison_project: str

    @classmethod
    def from_contract(cls, contract: EvaluateProjectsRequest, token: str):
        return cls(
            token=token,
            groundtruth_project=contract.groundtruth_project,
            comparison_project=contract.comparison_project,
        )
