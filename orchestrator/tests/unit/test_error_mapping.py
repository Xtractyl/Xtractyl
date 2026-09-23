# orchestrator/tests/unit/test_error_mapping.py

from http import HTTPStatus

from api.error_mapping import map_domain_error
from domain.errors import (
    AlreadyExists,
    DomainError,
    ExternalServiceError,
    InternalError,
    InvalidState,
    NotFound,
    Unauthorized,
    ValidationFailed,
)


def test_not_found_maps_to_404():
    status, code = map_domain_error(NotFound(code="X_NOT_FOUND", message="not found"))
    assert status == HTTPStatus.NOT_FOUND
    assert code == "X_NOT_FOUND"


def test_validation_failed_maps_to_400():
    status, code = map_domain_error(ValidationFailed(code="INVALID_COMMAND", message="bad"))
    assert status == HTTPStatus.BAD_REQUEST
    assert code == "INVALID_COMMAND"


def test_invalid_state_maps_to_409():
    status, code = map_domain_error(InvalidState(code="X_INVALID_STATE", message="bad state"))
    assert status == HTTPStatus.CONFLICT
    assert code == "X_INVALID_STATE"


def test_already_exists_maps_to_409():
    status, code = map_domain_error(AlreadyExists(code="X_ALREADY_EXISTS", message="exists"))
    assert status == HTTPStatus.CONFLICT
    assert code == "X_ALREADY_EXISTS"


def test_unauthorized_maps_to_401():
    status, code = map_domain_error(Unauthorized(code="X_UNAUTHORIZED", message="nope"))
    assert status == HTTPStatus.UNAUTHORIZED
    assert code == "X_UNAUTHORIZED"


def test_internal_error_maps_to_500():
    status, code = map_domain_error(InternalError(code="X_INTERNAL", message="boom"))
    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert code == "X_INTERNAL"


def test_external_service_error_maps_to_502_by_default():
    status, code = map_domain_error(ExternalServiceError(code="X_EXTERNAL", message="down"))
    assert status == HTTPStatus.BAD_GATEWAY
    assert code == "X_EXTERNAL"


def test_external_service_error_label_studio_unauthorized_maps_to_401():
    status, code = map_domain_error(
        ExternalServiceError(code="LABEL_STUDIO_UNAUTHORIZED", message="bad token")
    )
    assert status == HTTPStatus.UNAUTHORIZED
    assert code == "LABEL_STUDIO_UNAUTHORIZED"


def test_unknown_domain_error_falls_back_to_400():
    status, code = map_domain_error(DomainError(code="X_UNKNOWN", message="???"))
    assert status == HTTPStatus.BAD_REQUEST
    assert code == "X_UNKNOWN"
