# worker/infrastructure/orchestrator.py
from __future__ import annotations

import os
import time

import requests
from contracts.orchestrator import TaskResultRequest, TaskResultResponse
from domain.errors import ContractViolation, ExternalServiceError
from pydantic import ValidationError
from utils.logging_utils import dev_logger, safe_logger

ORCH_HOST = os.getenv("ORCH_CONTAINER_NAME", "orchestrator")
ORCH_PORT = os.getenv("ORCH_PORT", "5001")
ORCHESTRATOR_URL = f"http://{ORCH_HOST}:{ORCH_PORT}"

ORCH_TIMEOUT = 10
# An unreachable orchestrator is retried with doubling pauses (default 10s, 20s, 40s, 80s).
ORCH_MAX_ATTEMPTS = int(os.getenv("ORCH_MAX_ATTEMPTS", "5"))
ORCH_RETRY_DELAY_SECONDS = float(os.getenv("ORCH_RETRY_DELAY_SECONDS", "10"))


def _post(path: str, payload: dict) -> requests.Response:
    """POST to the orchestrator. Only a missing answer is retried, an answer (also an error one)
    is returned as it is."""
    delay = ORCH_RETRY_DELAY_SECONDS
    last_error: requests.RequestException | None = None
    for attempt in range(1, ORCH_MAX_ATTEMPTS + 1):
        try:
            return requests.post(f"{ORCHESTRATOR_URL}{path}", json=payload, timeout=ORCH_TIMEOUT)
        except requests.RequestException as e:
            last_error = e
            if attempt < ORCH_MAX_ATTEMPTS:
                time.sleep(delay)
                delay *= 2
    raise ExternalServiceError(
        code="ORCHESTRATOR_UNAVAILABLE",
        message="Orchestrator is unavailable.",
        meta={"attempts": ORCH_MAX_ATTEMPTS, "error": str(last_error)},
    ) from last_error


def send_job_failed(job_id: str, error: str | None) -> None:
    """Reports a failed run. Never raises: the run is failing anyway, so a lost report is only
    logged (the cleanup picks up runs that stay on 'running')."""
    try:
        resp = _post("/prelabel/job-failed", {"job_id": job_id, "error": error})
    except ExternalServiceError as e:
        safe_logger.error("send_job_failed_failed | job_id=%s", job_id, extra={"code": e.code})
        if dev_logger:
            dev_logger.error(
                "send_job_failed_failed_dev | job_id=%s",
                job_id,
                extra={"code": e.code, "meta": e.meta},
            )
        return
    if resp.status_code != 200:
        safe_logger.error(
            "send_job_failed_rejected | job_id=%s | status=%s",
            job_id,
            resp.status_code,
            extra={"code": "JOB_FAILED_REJECTED"},
        )

        if dev_logger:
            dev_logger.error(
                "send_job_failed_rejected_dev | job_id=%s | body=%s",
                job_id,
                resp.text,
                extra={"code": "JOB_FAILED_REJECTED"},
            )


def send_task_result(
    *,
    job_id: str,
    task_id: int,
    filename: str,
    success: bool,
    error: str | None,
    result: dict | None,
) -> bool:
    """Report the outcome of one task. Anything that goes wrong here raises a DomainError and
    ends the run. Returns False if the orchestrator tells the worker to stop (run cancelled)."""
    try:
        request = TaskResultRequest.model_validate(
            {
                "job_id": job_id,
                "task_id": task_id,
                "filename": filename,
                "success": success,
                "error": error,
                "result": result,
            }
        )
    except ValidationError as e:
        raise ContractViolation.from_validation_error(
            code="TASK_RESULT_INVALID",
            message="The task result does not match the contract with the orchestrator.",
            error=e,
        ) from e

    resp = _post("/prelabel/task-result", request.model_dump(mode="json"))

    if resp.status_code != 200:
        raise ExternalServiceError(
            code="TASK_RESULT_REJECTED",
            message=f"The orchestrator rejected a task result (HTTP {resp.status_code}).",
            meta={"status": resp.status_code, "body": resp.text},
        )
    try:
        return TaskResultResponse.model_validate(resp.json()).continue_
    except ValueError as e:  # invalid JSON or a ValidationError (a ValueError subclass)
        raise ContractViolation(
            code="ORCHESTRATOR_RESPONSE_INVALID",
            message="The answer of the orchestrator does not match the contract.",
            meta={"error": str(e)[:300]},
        ) from e
