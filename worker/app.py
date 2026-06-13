# worker/app.py
from __future__ import annotations

import json
import os

import redis
import requests
from contracts.jobs import JobPayload
from domain.prelabel_project import prelabel_project
from pydantic import ValidationError
from utils.logging_utils import dev_logger, safe_logger

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "job_queue"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

QUEUE = "prelabel_jobs"
STATUS = "status:"
RESULT = "result:"
LOGS = "logs:"

ORCHESTRATOR_URL = (
    f"http://{os.getenv('ORCH_CONTAINER_NAME', 'orchestrator')}:{os.getenv('ORCH_PORT', '5001')}"
)

USE_DB_BACKEND = os.getenv("USE_DB_BACKEND", "0") == "1"


def _status_key(job_id: str) -> str:
    return f"{STATUS}{job_id}"


def _result_key(job_id: str) -> str:
    return f"{RESULT}{job_id}"


def _logs_key(job_id: str) -> str:
    return f"{LOGS}{job_id}"


def _set_status(job_id: str, **kv) -> None:
    r.hset(_status_key(job_id), mapping=kv)


def _get_state(job_id: str) -> str | None:
    return r.hget(_status_key(job_id), "state")


def _add_log(job_id: str, line: str) -> None:
    r.rpush(_logs_key(job_id), line)


def _cancelled(job_id: str) -> bool:
    return _get_state(job_id) == "CANCEL_REQUESTED"


def _mark_cancelled(job_id: str) -> None:
    _set_status(job_id, state="CANCELLED")
    _add_log(job_id, "[INFO] Job cancelled.")


def _send_callback(job_id: str, status: str, error: str | None = None) -> None:
    try:
        requests.post(
            f"{ORCHESTRATOR_URL}/prelabel/callback",
            json={"job_id": job_id, "status": status, "error": error},
            timeout=10,
        )
    except requests.RequestException as e:
        safe_logger.error("prelabel_callback_failed | job_id=%s", job_id)
        if dev_logger:
            dev_logger.exception("prelabel_callback_failed_dev | error=%s", str(e))


def handle_job(job: JobPayload) -> None:
    job_id = job.job_id
    _set_status(job_id, state="RUNNING")
    _add_log(job_id, "[INFO] Worker picked up job.")

    try:
        logs = prelabel_project(
            job,
            log_cb=lambda line: _add_log(job_id, line),
            progress_cb=lambda pct: _set_status(job_id, progress=str(pct)),
            cancel_cb=lambda: _cancelled(job_id),
        )

        if _cancelled(job_id):
            _mark_cancelled(job_id)
            if USE_DB_BACKEND:
                _send_callback(job.job_id, "cancelled")
            return

        r.set(_result_key(job_id), json.dumps({"job_id": job_id, "logs_count": len(logs)}))

        final_state = _get_state(job_id) or "RUNNING"
        if final_state not in ("CANCELLED", "FAILED"):
            _set_status(job_id, state="SUCCEEDED", progress="100")
            if USE_DB_BACKEND:
                _send_callback(job.job_id, "done")

        _add_log(job_id, "[INFO] Job finished.")

    except Exception as e:
        _set_status(job_id, state="FAILED", error=str(e))
        if USE_DB_BACKEND:
            _send_callback(job.job_id, "failed", error=str(e))
        safe_logger.error("job_failed | job_id=%s", job_id)
        if dev_logger:
            dev_logger.exception("job_failed_dev | job_id=%s", job_id)


def main() -> None:
    safe_logger.info("worker_starting")
    while True:
        item = r.blpop(QUEUE, timeout=5)
        if not item:
            continue
        _, raw = item
        try:
            payload = json.loads(raw)
            job = JobPayload.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as e:
            safe_logger.error("invalid_payload")
            if dev_logger:
                dev_logger.exception("invalid_payload_dev | error=%s", str(e))
            continue
        handle_job(job)


if __name__ == "__main__":
    main()
