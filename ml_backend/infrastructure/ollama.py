# ml_backend/infrastructure/ollama.py
import os

import requests

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))


def ask_llm_with_timeout(prompt: str, model_name: str) -> dict:
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
            return {"answer": None, "status": "model_missing", "error": "model_not_available"}
        response.raise_for_status()
        ans = (response.json().get("response") or "").strip()
        return {"answer": ans if ans else None, "status": "ok", "error": None}
    except requests.exceptions.Timeout:
        return {"answer": None, "status": "failed", "error": "timeout"}
    except requests.exceptions.RequestException as e:
        return {"answer": None, "status": "failed", "error": str(e)}
