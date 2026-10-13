# worker/infrastructure/ml_backend.py
from __future__ import annotations

import os

import requests
from contracts.jobs import JobPayload
from contracts.ml_backend import ErrorResponse, PredictMeta, PredictRequest, PredictResponse
from domain.errors import ContractViolation, ExternalServiceError
from pydantic import ValidationError

ML_HOST = os.getenv("ML_BACKEND_HOST", "ml_backend")
ML_PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))
ML_BASE = os.getenv("ML_BACKEND_BASE", f"http://{ML_HOST}:{ML_PORT}")

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
LLM_OVERHEAD = int(os.getenv("LLM_OVERHEAD", "5"))
UPLOAD_MARGIN = int(os.getenv("UPLOAD_MARGIN", "30"))


def _build_request(*, task_id: int, html: str | None, filename: str, job: JobPayload) -> dict:
    try:
        request = PredictRequest.model_validate(
            {
                "job_id": job.job_id,
                "task_id": str(task_id),
                "filename": filename,
                "html": html,
                "questions_and_labels": job.questions_and_labels.model_dump(),
                "llm_config": {
                    "ollama_model": job.model,
                    "system_prompt": job.system_prompt,
                },
                "label_studio_config": {
                    "ls_token": job.token,
                },
            }
        )
    except ValidationError as e:
        raise ContractViolation.from_validation_error(
            code="ML_REQUEST_INVALID",
            message="The request to the ML backend does not match the contract.",
            error=e,
        ) from e
    return request.model_dump()


def _error_from_response(resp: requests.Response) -> ExternalServiceError:
    """Takes over code and message of the ml_backend's error answer if it has one."""
    try:
        err = ErrorResponse.model_validate(resp.json())
    except (ValueError, ValidationError):
        return ExternalServiceError(
            code="ML_BACKEND_HTTP_ERROR",
            message=f"The ML backend answered with HTTP {resp.status_code}.",
            meta={"status": resp.status_code, "body": resp.text[:500]},
        )
    return ExternalServiceError(
        code=err.error, message=err.message, meta={"status": resp.status_code}
    )


def predict(*, task_id: int, html: str | None, filename: str, job: JobPayload) -> PredictMeta:
    """Asks the ml_backend to prelabel one task. Raises a DomainError for everything that goes
    wrong with this one task; the caller decides what that means for the task and the run."""
    payload = _build_request(task_id=task_id, html=html, filename=filename, job=job)

    q_count = max(1, len(job.questions_and_labels.questions))
    request_timeout = q_count * (LLM_TIMEOUT + LLM_OVERHEAD) + UPLOAD_MARGIN

    try:
        resp = requests.post(f"{ML_BASE}/predict", json=payload, timeout=request_timeout)
    except requests.ConnectionError as e:
        raise ExternalServiceError(
            code="ML_BACKEND_UNAVAILABLE",
            message="ML backend is unavailable.",
            meta={"error": str(e)},
        ) from e
    except requests.Timeout as e:
        raise ExternalServiceError(
            code="ML_BACKEND_TIMEOUT",
            message="ML backend did not answer in time.",
            meta={"error": str(e), "timeout_s": request_timeout},
        ) from e
    except requests.RequestException as e:
        raise ExternalServiceError(
            code="ML_BACKEND_UNAVAILABLE",
            message="ML backend is unavailable.",
            meta={"error": str(e)},
        ) from e

    if resp.status_code != 200:
        raise _error_from_response(resp)

    try:
        return PredictResponse.model_validate(resp.json()).meta
    except ValueError as e:  # invalid JSON or a ValidationError (a ValueError subclass)
        if isinstance(e, ValidationError):
            raise ContractViolation.from_validation_error(
                code="ML_RESPONSE_INVALID",
                message="The answer of the ML backend does not match the contract.",
                error=e,
            ) from e
        raise ContractViolation(
            code="ML_RESPONSE_INVALID",
            message="The answer of the ML backend is not valid JSON.",
        ) from e
