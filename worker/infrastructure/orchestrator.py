# worker/infrastructure/orchestrator.py
from __future__ import annotations

import os

import requests
from utils.logging_utils import dev_logger, safe_logger

ORCH_HOST = os.getenv("ORCH_CONTAINER_NAME", "orchestrator")
ORCH_PORT = os.getenv("ORCH_PORT", "5001")
ORCHESTRATOR_URL = f"http://{ORCH_HOST}:{ORCH_PORT}"

def send_job_failed(job_id: str, error: str) -> None:
    try:
        requests.post(
            f"{ORCHESTRATOR_URL}/prelabel/job-failed",
            json={"job_id": job_id, "error": error},
            timeout=10,
        )
    except requests.RequestException as e:
        safe_logger.error("send_job_failed_failed | job_id=%s", job_id)
        if dev_logger:
            dev_logger.exception("send_job_failed_failed_dev | error=%s", str(e))


def send_task_result(
    *,
    job_id: str,
    task_id: int,
    filename: str,
    success: bool,
    error: str | None,
    result: dict | None,
) -> bool:
    """Report the outcome of one task. A rejected or unreachable call raises and fails the whole run.
    Returns False if the orchestrator tells the worker to stop (run cancelled)."""

    payload = {
        "job_id": job_id,
        "task_id": task_id,
        "filename": filename,
        "success": success,
        "error": error,
        "result": result,
    }
    try:
        resp = requests.post(
            f"{ORCHESTRATOR_URL}/prelabel/task-result",
            json=payload,
            timeout=10,
        )
    except requests.RequestException as e:
        safe_logger.error("send_task_result_failed | job_id=%s | task_id=%s", job_id, task_id)
        if dev_logger:
            dev_logger.exception("send_task_result_failed_dev | error=%s", str(e))
        raise
    if resp.status_code != 200:
        safe_logger.error(
            "send_task_result_rejected | job_id=%s | task_id=%s | status=%s",
            job_id,
            task_id,
            resp.status_code,
        )
        if dev_logger:
            dev_logger.error("send_task_result_rejected_dev | body=%s", resp.text)
        raise RuntimeError(f"task-result rejected for task {task_id}: HTTP {resp.status_code}")
    return bool(resp.json()["continue"])
