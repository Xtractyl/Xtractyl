# orchestrator/infrastructure/queue/redis_queue.py
import json
import time

import redis
from domain.errors import ExternalServiceError
from infrastructure.interfaces.queue import ConversionQueueInterface, PrelabelQueueInterface


class RedisJobQueue:
    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        queue_name: str,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.5,
    ):
        self._client = redis.Redis(host=host, port=port, db=db)
        self._queue_name = queue_name
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

    def _push(self, payload: dict) -> None:
        serialized = json.dumps(payload)
        last_error = None
        for attempt in range(self._max_retries):
            try:
                self._client.rpush(self._queue_name, serialized)
                return
            except redis.RedisError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay_seconds)
        raise ExternalServiceError(
            code="REDIS_UNAVAILABLE",
            message="Could not push job to queue.",
        ) from last_error


class RedisConversionQueue(RedisJobQueue, ConversionQueueInterface):
    def push_conversion_job(self, job_id: int, project: str, pdf_keys: list[str]) -> None:
        self._push({"job_id": job_id, "project": project, "pdf_keys": pdf_keys})


class RedisPrelabelQueue(RedisJobQueue, PrelabelQueueInterface):
    def push_prelabel_job(self, payload: dict) -> None:
        self._push(payload)
