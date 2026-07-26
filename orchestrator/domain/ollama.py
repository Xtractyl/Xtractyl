# orchestrator/domain/ollama.py


import os

from domain.models.ollama import ListModelsCommand, PullModelCommand

ARCHIVE_PREFIX = os.getenv("XTRACTYL_MODEL_ARCHIVE_PREFIX", "xtractyl-archive")


def list_models(cmd: ListModelsCommand, ollama_client) -> dict:
    models = ollama_client.list_tags()
    return {
        "models": [
            m.get("model") or m.get("name")
            for m in models
            if (m.get("model") or m.get("name") or "").startswith(f"{ARCHIVE_PREFIX}/")
        ]
    }


def pull_model(cmd: PullModelCommand, ollama_client):
    yield from ollama_client.pull(cmd.model)
