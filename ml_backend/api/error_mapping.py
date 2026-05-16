# ml_backend/api/error_mapping.py
from domain.errors import (
    DomainError,
    ExternalServiceError,
    InternalError,
    NotFound,
    ValidationFailed,
)


def map_domain_error(err: DomainError) -> tuple[int, str]:
    match err:
        case ValidationFailed():
            return 422, err.code
        case NotFound():
            return 404, err.code
        case ExternalServiceError():
            return 502, err.code
        case InternalError():
            return 500, err.code
        case _:
            return 500, err.code
