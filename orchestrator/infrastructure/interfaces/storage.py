# orchestrator/infrastructure/interfaces/storage.py
from abc import ABC, abstractmethod


class StorageInterface(ABC):
    @abstractmethod
    def ensure_bucket(self) -> None: ...

    @abstractmethod
    def presigned_put(self, key: str) -> str: ...

    @abstractmethod
    def presigned_get(self, key: str) -> str: ...
