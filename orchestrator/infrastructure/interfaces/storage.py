# orchestrator/infrastructure/interfaces/storage.py
from abc import ABC, abstractmethod


class StorageInterface(ABC):
    @abstractmethod
    def ensure_bucket(self) -> None: ...

    @abstractmethod
    def presigned_put(self, key: str) -> str: ...

    @abstractmethod
    def get_object(self, key: str) -> str: ...

    @abstractmethod  # deletes remnants of failed conversion by the prefix (project name) in the pdf/html key
    def delete_prefix(self, prefix: str) -> None: ...

    @abstractmethod  # every top-level prefix (project name folder) currently in the bucket
    def list_top_level_prefixes(self) -> list[str]: ...
