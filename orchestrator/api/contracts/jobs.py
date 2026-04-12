# orchestrator/api/contracts/jobs.py

from pydantic import BaseModel, Field


class PLACEHOLDERRequest(BaseModel):
    project_name: str = Field(..., min_length=1)


class PLACEHOLDERResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    total: int
    results_output_path_csv: str
