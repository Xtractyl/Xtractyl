# /ml_backend/client.py

import requests


def ask_llm_with_timeout(params, prompt: str, timeout: int, model_name: str) -> dict:
    base = params["ollama_base"]

    try:
        response = requests.post(
            f"{base}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "seed": 42},
            },
            timeout=timeout,
        )
        if response.status_code == 404:
            return {"answer": None, "status": "model_missing", "error": "model_not_available"}
        response.raise_for_status()
        ans = (response.json().get("response") or "").strip()
        return {"answer": ans if ans else None, "status": "ok", "error": None}
    except requests.exceptions.Timeout:
        return {"answer": None, "status": "timeout", "error": "timeout"}
    except Exception as e:
        return {"answer": None, "status": "error", "error": str(e)}
