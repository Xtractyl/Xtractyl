# worker_conversion/config.py
from __future__ import annotations

import os

WORKER_DOCLING_TIMEOUT_SECONDS = int(os.getenv("WORKER_DOCLING_TIMEOUT_SECONDS", "300"))

REDIS_HOST = os.getenv("REDIS_HOST", "job_queue")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
QUEUE = "conversion_jobs"

MINIO_ENDPOINT = (
    os.getenv("MINIO_CONTAINER_NAME", "minio") + ":" + os.getenv("MINIO_API_PORT", "9000")
)
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "yourpassword")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "xtractyl")

DOCLING_URL = (
    f"http://{os.getenv('DOCLING_CONTAINER_NAME', 'docling')}:{os.getenv('DOCLING_PORT', '5004')}"
)
ORCHESTRATOR_CALLBACK_URL = f"http://{os.getenv('ORCH_CONTAINER_NAME', 'orchestrator')}:{os.getenv('ORCH_PORT', '5001')}/conversion/callback"
