# ml_backend/api/error_handler.py
import os
import traceback

from api.contracts.errors import ErrorResponse
from api.error_mapping import map_domain_error
from domain.errors import DomainError, ValidationFailed
from flask import jsonify

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS") == "1"


def register_error_handlers(app, logger_safe, logger_dev):
    @app.errorhandler(DomainError)
    def handle_domain_error(err: DomainError):
        status, code = map_domain_error(err)

        logger_safe.info(
            "domain_error",
            extra={"code": code, "error_message": err.message},
        )

        if DEBUG_ARTIFACTS and logger_dev:
            logger_dev.info(
                "domain_error_dev",
                extra={
                    "code": code,
                    "meta": err.meta,
                    "traceback": traceback.format_exc(),
                },
            )

        details = None
        if isinstance(err, ValidationFailed) and err.details:
            details = []
            for d in err.details:
                if not isinstance(d, dict):
                    continue
                details.append(
                    {
                        "loc": d.get("loc"),
                        "msg": d.get("msg", "Invalid value."),
                        "type": d.get("type"),
                    }
                )

        payload = ErrorResponse(
            error=code,
            message=err.message,
            details=details,
        ).model_dump()

        return jsonify(payload), int(status)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        logger_safe.error("unexpected_error")

        if DEBUG_ARTIFACTS and logger_dev:
            logger_dev.exception("unexpected_error_dev")

        payload = ErrorResponse(
            error="INTERNAL_ERROR",
            message="Unexpected server error.",
        ).model_dump()

        return jsonify(payload), 500
