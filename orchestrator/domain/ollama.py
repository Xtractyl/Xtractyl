# orchestrator/domain/ollama.py

import os

import requests

from domain.errors import ExternalServiceError
from domain.models.ollama import ListModelsCommand, PullModelCommand

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")


def list_models(cmd: ListModelsCommand) -> dict:
    """
    List all locally available Ollama models.

    Args:
        cmd: ListModelsCommand (no input needed).

    Returns:
        {"models": list[str]}

    Raises:
        ExternalServiceError: If Ollama is unreachable.
    """
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=10)
        res.raise_for_status()
        data = res.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="OLLAMA_UNAVAILABLE",
            message="Could not reach Ollama.",
        )
    models = data.get("models") or []
    return {
        "models": [
            m.get("model") or m.get("name") for m in models if m.get("model") or m.get("name")
        ]
    }


def pull_model(cmd: PullModelCommand):
    """
    Stream a model pull from Ollama.

    Args:
        cmd: PullModelCommand with model name.

    Yields:
        Raw NDJSON lines from Ollama pull stream.

    Raises:
        ExternalServiceError: If Ollama is unreachable.
    """
    try:
        with requests.post(
            f"{OLLAMA_BASE}/api/pull",
            json={"name": cmd.model},
            stream=True,
            timeout=300,
        ) as res:
            res.raise_for_status()
            for line in res.iter_lines():
                if line:
                    yield line + b"\n"
    except requests.RequestException:
        raise ExternalServiceError(
            code="OLLAMA_UNAVAILABLE",
            message="Could not reach Ollama.",
        )
