# worker/app.py
from __future__ import annotations

import json
import os

import redis
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
            return

        r.set(_result_key(job_id), json.dumps({"job_id": job_id, "logs_count": len(logs)}))

        final_state = _get_state(job_id) or "RUNNING"
        if final_state not in ("CANCELLED", "FAILED"):
            _set_status(job_id, state="SUCCEEDED", progress="100")

        _add_log(job_id, "[INFO] Job finished.")

    except Exception as e:
        _set_status(job_id, state="FAILED", error=str(e))
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
