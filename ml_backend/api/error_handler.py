# ml_backend/api/error_handler.py
import os
import traceback

from domain.errors import DomainError, ValidationFailed
from flask import g, jsonify

from api.contracts.errors import ErrorResponse
from api.error_mapping import map_domain_error

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS") == "1"


def _ids() -> str:
    return f"job_id={g.get('job_id', '-')} task_id={g.get('task_id', '-')}"


def register_error_handlers(app, logger_safe, logger_dev):
    @app.errorhandler(DomainError)
    def handle_domain_error(err: DomainError):
        status, code = map_domain_error(err)

        logger_safe.info(
            f"domain_error | {_ids()}",
            extra={"code": code, "error_message": err.message},
        )

        if DEBUG_ARTIFACTS and logger_dev:
            logger_dev.info(
                f"domain_error_dev | {_ids()}",
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
        logger_safe.error(f"unexpected_error | {_ids()}", extra={"code": "INTERNAL_ERROR"})

        if DEBUG_ARTIFACTS and logger_dev:
            logger_dev.exception(f"unexpected_error_dev | {_ids()}")

        payload = ErrorResponse(
            error="INTERNAL_ERROR",
            message="Unexpected server error.",
        ).model_dump()

        return jsonify(payload), 500
