# orchestrator/domain/errors.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DomainError(Exception):
    code: str
    message: str
    meta: Optional[Dict[str, Any]] = None


@dataclass
class NotFound(DomainError):
    pass


@dataclass
class InvalidState(DomainError):
    pass


@dataclass
class ValidationFailed(DomainError):
    details: Optional[list] = None


@dataclass
class ExternalServiceError(DomainError):
    pass
