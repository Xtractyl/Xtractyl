# /ml_backend/client.py
import requests

import logging

def ensure_model_available(params, model_name: str):
    base = params["ollama_base"]
    try:
        r = requests.get(f"{base}/api/tags", timeout=10)
        r.raise_for_status()
        local_models = [m.get("name") or m.get("model") for m in r.json().get("models", [])]
        local_models = [m for m in local_models if m]
        if model_name in local_models:
            return True

        logging.info(f"📦 Model '{model_name}' not present — pulling…")
        pull = requests.post(
            f"{base}/api/pull", json={"name": model_name}, stream=True, timeout=600
        )
        for line in pull.iter_lines():
            if line:
                logging.debug("📥 %s", line.decode("utf-8"))
        logging.info(f"✅ Model '{model_name}' pulled.")
        return True
    except Exception as e:
        logging.error(f"❌ Error ensuring model '{model_name}': {e}")
        return False


def ask_llm_with_timeout(params, prompt: str, timeout: int, model_name: str) -> dict:
    """
    Returns:
      {"answer": str|None, "status": "ok"|"timeout"|"error"|"model_missing", "error": str|None}
    """
    base = params["ollama_base"]

    if not ensure_model_available(params, model_name):
        return {"answer": None, "status": "model_missing", "error": "model_not_available"}

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
        response.raise_for_status()

        ans = (response.json().get("response") or "").strip()
        return {"answer": ans if ans else None, "status": "ok", "error": None}

    except requests.exceptions.Timeout:
        return {"answer": None, "status": "timeout", "error": "timeout"}

    except Exception as e:
        return {"answer": None, "status": "error", "error": str(e)}