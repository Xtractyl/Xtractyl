# orchestrator/api/error_handler.py

import os
import traceback

from domain.errors import DomainError, ValidationFailed
from flask import g, jsonify

from api.contracts.errors import ErrorResponse
from api.error_mapping import map_domain_error

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS") == "1"


def register_error_handlers(app, logger_safe, logger_dev):
    @app.errorhandler(DomainError)
    def handle_domain_error(err: DomainError):
        status, code = map_domain_error(err)

        # ---- safe logging (default) ----
        logger_safe.info(
            "domain_error",
            extra={
                "code": code,
                "error_message": err.message,
                "request_id": getattr(g, "request_id", None),
            },
        )

        # ---- dev logging (opt-in) ----
        if DEBUG_ARTIFACTS:
            logger_dev.info(
                "domain_error_dev",
                extra={
                    "code": code,
                    "meta": err.meta,
                    "traceback": traceback.format_exc(),
                    "request_id": getattr(g, "request_id", None),
                },
            )
        details = None
        if isinstance(err, ValidationFailed) and err.details:
            # Only forward a safe subset of pydantic error entries
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
            request_id=getattr(g, "request_id", None),
            details=details,
        ).model_dump()

        return jsonify(payload), int(status)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        # ---- safe logging: NO traceback ----
        logger_safe.error(
            "unexpected_error",
            extra={"request_id": getattr(g, "request_id", None)},
        )

        # ---- dev logging: traceback allowed ----
        if DEBUG_ARTIFACTS:
            logger_dev.exception(
                "unexpected_error_dev",
                extra={"request_id": getattr(g, "request_id", None)},
            )

        payload = ErrorResponse(
            error="INTERNAL_ERROR",
            message="Unexpected server error.",
            request_id=getattr(g, "request_id", None),
        ).model_dump()

        return jsonify(payload), 500
