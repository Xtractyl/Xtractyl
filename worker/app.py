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

ORCHESTRATOR_URL = (
    f"http://{os.getenv('ORCH_CONTAINER_NAME', 'orchestrator')}:{os.getenv('ORCH_PORT', '5001')}"
)


def _report_job_failed(job_id: str, error: str) -> None:
    try:
        requests.post(
            f"{ORCHESTRATOR_URL}/prelabel/job-failed",
            json={"job_id": job_id, "error": error},
            timeout=10,
        )
    except requests.RequestException as e:
        safe_logger.error("job_failed_report_failed | job_id=%s", job_id)
        if dev_logger:
            dev_logger.exception("job_failed_report_failed_dev | error=%s", str(e))


def handle_job(job: JobPayload) -> None:
    safe_logger.info("job_picked_up | job_id=%s", job.job_id)
    try:
        prelabel_project(job)
    except Exception as e:
        _report_job_failed(job.job_id, str(e))
        safe_logger.error("job_failed | job_id=%s", job.job_id)
        if dev_logger:
            dev_logger.exception("job_failed_dev | job_id=%s", job.job_id)


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
