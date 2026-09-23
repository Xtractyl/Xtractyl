# worker_conversion/consumer.py
from __future__ import annotations

import json

from config import QUEUE
from domain import handle_job
from minio import Minio
from contracts import ConversionJobPayload
from pydantic import ValidationError
from redis import Redis
from utils.logging_utils import dev_logger, safe_logger


def run(redis_conn: Redis, minio_client: Minio) -> None:
    safe_logger.info("worker_conversion_starting")
    while True:
        item = redis_conn.blpop(QUEUE, timeout=5)
        if not item:
            continue
        _, raw = item
        try:
            job = ConversionJobPayload.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            safe_logger.error("invalid_conversion_payload | error=%s", str(e))
            if dev_logger:
                dev_logger.exception("invalid_conversion_payload_dev | error=%s", str(e))
            continue
        try:
            handle_job(job, minio_client)
        except Exception as e:
            safe_logger.error(
                "conversion_job_crashed | job_id=%s", getattr(job, "job_id", "unknown")
            )
            if dev_logger:
                dev_logger.exception(
                    "conversion_job_crashed_dev | job_id=%s | error=%s",
                    getattr(job, "job_id", "unknown"),
                    str(e),
                )
