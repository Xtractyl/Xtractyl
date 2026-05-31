# orchestrator/infrastructure/interfaces/queue.py
from abc import ABC, abstractmethod


class QueueInterface(ABC):
    @abstractmethod
    def push_conversion_job(
        self,
        job_id: int,
        project: str,
        pdf_keys: list[str],
        minio_bucket: str,
    ) -> None: ...
