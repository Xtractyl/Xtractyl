# worker/app.py
from __future__ import annotations

import json
import os

import redis
from contracts.jobs import JobPayload
from pydantic import ValidationError
from utils.logging_utils import dev_logger, safe_logger
from domain.jobs import run_job

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "job_queue"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

QUEUE = "prelabel_jobs"

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
        run_job(job)


if __name__ == "__main__":
    main()
