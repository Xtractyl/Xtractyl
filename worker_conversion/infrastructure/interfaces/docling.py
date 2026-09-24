# worker_conversion/infrastructure/interfaces/docling.py
from abc import ABC, abstractmethod


class DoclingClientInterface(ABC):
    @abstractmethod
    def convert(self, filename: str, pdf_bytes: bytes) -> str: ...
