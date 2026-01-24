# orchestrator/api/contracts/results.py

from pydantic import BaseModel, Field


class GetResultsTableRequest(BaseModel):
    project_name: str = Field(..., min_length=1)
