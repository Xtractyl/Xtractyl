# worker/app.py
from __future__ import annotations

import json
import os
import time

import redis
from contracts.jobs import JobPayload
from domain.jobs import run_job
from infrastructure.orchestrator import send_job_failed
from pydantic import ValidationError
from utils.logging_utils import dev_logger, safe_logger

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "job_queue"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

QUEUE = "prelabel_jobs"

REDIS_RETRY_DELAY_SECONDS = float(os.getenv("REDIS_RETRY_DELAY_SECONDS", "5"))
REDIS_RETRY_MAX_DELAY_SECONDS = float(os.getenv("REDIS_RETRY_MAX_DELAY_SECONDS", "60"))


def _extract_job_id(raw: str) -> str | None:
    """The job id of a payload that is otherwise unusable, if it has one."""
    try:
        job_id = json.loads(raw).get("job_id")
    except (ValueError, AttributeError):
        return None
    if isinstance(job_id, (str, int)) and not isinstance(job_id, bool) and str(job_id):
        return str(job_id)
    return None


def _handle_invalid_payload(raw: str, error: Exception) -> None:
    safe_logger.error("invalid_payload", extra={"code": "INVALID_PAYLOAD"})
    if dev_logger:
        dev_logger.error(
            "invalid_payload_dev | error=%s | payload=%s",
            error,
            raw,
            extra={"code": "INVALID_PAYLOAD"},
        )
    job_id = _extract_job_id(raw)
    if job_id is not None:
        send_job_failed(job_id, None)


def main() -> None:
    safe_logger.info("worker_starting")
    redis_down = False
    delay = REDIS_RETRY_DELAY_SECONDS
    while True:
        try:
            item = r.blpop(QUEUE, timeout=5)
        except redis.RedisError as e:
            if not redis_down:  # one log entry per outage, not one per attempt
                redis_down = True
                safe_logger.error("redis_unavailable", extra={"code": "REDIS_UNAVAILABLE"})
                if dev_logger:
                    dev_logger.error(
                        "redis_unavailable_dev | error=%s", e, extra={"code": "REDIS_UNAVAILABLE"}
                    )
            time.sleep(delay)
            delay = min(delay * 2, REDIS_RETRY_MAX_DELAY_SECONDS)
            continue
        if redis_down:
            safe_logger.info("redis_recovered")
            redis_down = False
            delay = REDIS_RETRY_DELAY_SECONDS
        if not item:
            continue
        _, raw = item
        try:
            job = JobPayload.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            _handle_invalid_payload(raw, e)
            continue
        run_job(job)


if __name__ == "__main__":
    main()
