# ml_backend/infrastructure/ollama.py
import os

import requests
from domain.errors import ExternalServiceError

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))


def ask_llm_with_timeout(prompt: str, model_name: str) -> str | None:
    """Ask Ollama one question. Returns the answer, or None if the model answered with an empty text.
    Raises ExternalServiceError: LLM_MODEL_MISSING, LLM_TIMEOUT or LLM_CALL_FAILED.
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "seed": 42, "num_ctx": LLM_NUM_CTX},
            },
            timeout=LLM_TIMEOUT,
        )
        if response.status_code == 404:
            raise ExternalServiceError(
                code="LLM_MODEL_MISSING",
                message="The model is not available in Ollama.",
                meta={"model": model_name},
            )
        response.raise_for_status()
        answer = (response.json().get("response") or "").strip()
    except requests.exceptions.Timeout as e:
        raise ExternalServiceError(
            code="LLM_TIMEOUT",
            message="The LLM did not answer in time.",
            meta={"model": model_name, "timeout_seconds": LLM_TIMEOUT},
        ) from e
    except (requests.exceptions.RequestException, ValueError) as e:
        raise ExternalServiceError(
            code="LLM_CALL_FAILED",
            message="The LLM call failed.",
            meta={"model": model_name, "error": str(e)},
        ) from e
    return answer or None
