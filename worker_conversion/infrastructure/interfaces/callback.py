# worker_conversion/infrastructure/interfaces/callback.py
from abc import ABC, abstractmethod


class CallbackClientInterface(ABC):
    @abstractmethod
    def send(
        self,
        job_id: int,
        filename: str,
        html_key: str | None,
        success: bool,
        error: str | None = None,
        pdf_hash: str | None = None,
        html_hash: str | None = None,
    ) -> bool: ...
