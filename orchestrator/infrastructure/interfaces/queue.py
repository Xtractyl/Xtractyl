# orchestrator/infrastructure/interfaces/queue.py
from abc import ABC, abstractmethod


class ConversionQueueInterface(ABC):
    @abstractmethod
    def push_conversion_job(
        self,
        job_id: int,
        project: str,
        pdf_keys: list[str],
    ) -> None: ...


class PrelabelQueueInterface(ABC):
    @abstractmethod
    def push_prelabel_job(self, payload: dict) -> None: ...
