# worker/infrastructure/ml_backend.py
from __future__ import annotations

import os

import requests
from contracts.jobs import JobPayload
from domain.errors import ExternalServiceError

from infrastructure.label_studio import LS_BASE

ML_HOST = os.getenv("ML_BACKEND_HOST", "ml_backend")
ML_PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))
ML_BASE = os.getenv("ML_BACKEND_BASE", f"http://{ML_HOST}:{ML_PORT}")
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")


LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
LLM_OVERHEAD = int(os.getenv("LLM_OVERHEAD", "5"))
UPLOAD_MARGIN = int(os.getenv("UPLOAD_MARGIN", "30"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))


def send_predict(*, task_id: int, html: str, job: JobPayload) -> requests.Response:
    url = f"{ML_BASE}/predict"

    q_count = max(1, len(job.questions_and_labels.questions))
    request_timeout = q_count * (LLM_TIMEOUT + LLM_OVERHEAD) + UPLOAD_MARGIN

    payload = {
        "job_id": job.job_id,
        "task_id": str(task_id),
        "html": html,
        "questions_and_labels": job.questions_and_labels.model_dump(),
        "llm_config": {
            "ollama_model": job.model,
            "ollama_base": OLLAMA_BASE,
            "system_prompt": job.system_prompt,
            "llm_timeout_seconds": LLM_TIMEOUT,
            "num_ctx": LLM_NUM_CTX,
        },
        "label_studio_config": {
            "label_studio_url": LS_BASE,
            "ls_token": job.token,
        },
    }

    try:
        return requests.post(url, json=payload, timeout=request_timeout)
    except requests.RequestException:
        raise ExternalServiceError(
            code="ML_BACKEND_UNAVAILABLE",
            message="ML backend is unavailable.",
        )
