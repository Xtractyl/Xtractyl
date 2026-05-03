# orchestrator/api/contracts/ollama.py

from pydantic import BaseModel


class ListModelsResponse(BaseModel):
    models: list[str]
