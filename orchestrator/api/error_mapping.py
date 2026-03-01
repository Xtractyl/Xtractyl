# orchestrator/api/error_mapping.py
from http import HTTPStatus

from domain.errors import (
    DomainError,
    ExternalServiceError,
    InvalidState,
    NotFound,
    ValidationFailed,
)


def map_domain_error(err: DomainError) -> tuple[int, str]:
    if isinstance(err, NotFound):
        return HTTPStatus.NOT_FOUND, err.code

    if isinstance(err, ValidationFailed):
        return HTTPStatus.BAD_REQUEST, err.code

    if isinstance(err, InvalidState):
        return HTTPStatus.CONFLICT, err.code

    if isinstance(err, ExternalServiceError):
        if err.code == "LABEL_STUDIO_UNAUTHORIZED":
            return HTTPStatus.UNAUTHORIZED, err.code
        return HTTPStatus.BAD_GATEWAY, err.code

    return HTTPStatus.BAD_REQUEST, err.code
