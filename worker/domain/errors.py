# worker/domain/errors.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from pydantic import ValidationError


@dataclass
class DomainError(Exception):
    code: str
    message: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass
class ExternalServiceError(DomainError):
    pass


@dataclass
class InvalidState(DomainError):
    pass


@dataclass
class ContractViolation(DomainError):
    @classmethod
    def from_validation_error(
        cls, code: str, message: str, error: ValidationError
    ) -> "ContractViolation":
        problems = [{"loc": [str(p) for p in e["loc"]], "type": e["type"]} for e in error.errors()]
        return cls(code=code, message=message, meta={"errors": problems})
