# orchestrator/api/contracts/results.py

from pydantic import BaseModel, Field


class GetResultsTableRequest(BaseModel):
    project_name: str = Field(..., min_length=1)


class GetResultsTableResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    total: int
    results_output_path_csv: str
