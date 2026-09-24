# worker_conversion/infrastructure/interfaces/storage.py
from abc import ABC, abstractmethod


class ConversionStorageInterface(ABC):
    @abstractmethod
    def get_object(self, bucket: str, key: str) -> bytes: ...

    @abstractmethod
    def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
