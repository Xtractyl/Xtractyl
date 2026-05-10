# worker/infrastructure/ml_backend.py
from __future__ import annotations

import os
from typing import Any, Dict

import requests

from contracts.jobs import JobPayload
from domain.errors import ExternalServiceError
from infrastructure.label_studio import LS_BASE

ML_HOST = os.getenv("ML_BACKEND_HOST", "ml_backend")
ML_PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))
ML_BASE = os.getenv("ML_BACKEND_BASE", f"http://{ML_HOST}:{ML_PORT}")

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
LLM_OVERHEAD = int(os.getenv("LLM_OVERHEAD", "5"))
UPLOAD_MARGIN = int(os.getenv("UPLOAD_MARGIN", "30"))


def send_predict(*, task_id: int, html: str, job: JobPayload) -> requests.Response:
    url = f"{ML_BASE}/predict"

    q_count = max(1, len(job.questions_and_labels.questions))
    request_timeout = q_count * (LLM_TIMEOUT + LLM_OVERHEAD) + UPLOAD_MARGIN

    payload: Dict[str, Any] = {
        "task_id": task_id,
        "html": html,
        "job_id": job.job_id,
        "model": job.model,
        "system_prompt": job.system_prompt,
        "token": job.token,
        "questions_and_labels": job.questions_and_labels.model_dump(),
        "questions": job.questions_and_labels.questions,
        "labels": job.questions_and_labels.labels,
        "params": {
            "label_studio_url": LS_BASE,  # war Walrus-Konstrukt
            "ls_token": job.token,
            "ollama_model": job.model,
            "ollama_base": os.getenv("OLLAMA_BASE", "http://ollama:11434"),
            "system_prompt": job.system_prompt,
            "llm_timeout_seconds": LLM_TIMEOUT,
        },
    }

    try:
        return requests.post(url, json=payload, timeout=request_timeout)
    except requests.RequestException:
        raise ExternalServiceError(
            code="ML_BACKEND_UNAVAILABLE",
            message="ML backend is unavailable.",
        )
