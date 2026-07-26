# orchestrator/infrastructure/ollama/ollama_client.py
import requests
from domain.errors import ExternalServiceError


class OllamaClient:
    def __init__(self, base_url: str):
        self._base_url = base_url

    def list_tags(self) -> list[dict]:
        try:
            res = requests.get(f"{self._base_url}/api/tags", timeout=10)
            res.raise_for_status()
        except requests.RequestException:
            raise ExternalServiceError(
                code="OLLAMA_UNAVAILABLE",
                message="Could not reach Ollama.",
            )
        return res.json().get("models") or []

    def copy(self, source: str, destination: str) -> None:
        try:
            res = requests.post(
                f"{self._base_url}/api/copy",
                json={"source": source, "destination": destination},
                timeout=30,
            )
            res.raise_for_status()
        except requests.RequestException:
            raise ExternalServiceError(
                code="OLLAMA_UNAVAILABLE",
                message=f"Could not copy model {source} -> {destination}.",
            )

    def pull(self, model: str):
        try:
            with requests.post(
                f"{self._base_url}/api/pull",
                json={"name": model},
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
