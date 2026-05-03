# orchestrator/api/contracts/ollama.py

from pydantic import BaseModel, Field


class ListModelsResponse(BaseModel):
    models: list[str]


class PullModelRequest(BaseModel):
    model: str = Field(..., min_length=1)


class PullModelResponse(BaseModel):
    pass  # streaming response, no validation
