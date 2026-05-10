# worker/domain/errors.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DomainError(Exception):
    code: str
    message: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass
class NotFound(DomainError):
    pass


@dataclass
class ExternalServiceError(DomainError):
    pass
