# orchestrator/infrastructure/queue/redis_queue.py
import json

import redis
from domain.errors import ExternalServiceError
from infrastructure.interfaces.queue import QueueInterface


class RedisQueue(QueueInterface):
    def __init__(self, host: str, port: int, db: int, queue_name: str):
        self._client = redis.Redis(host=host, port=port, db=db)
        self._queue_name = queue_name

    def push_conversion_job(
        self,
        job_id: int,
        project: str,
        pdf_keys: list[str],
    ) -> None:
        try:
            self._client.rpush(
                self._queue_name,
                json.dumps(
                    {
                        "job_id": job_id,
                        "project": project,
                        "pdf_keys": pdf_keys,
                    }
                ),
            )
        except redis.RedisError as e:
            raise ExternalServiceError(
                code="REDIS_UNAVAILABLE",
                message="Could not push job to queue.",
            ) from e
