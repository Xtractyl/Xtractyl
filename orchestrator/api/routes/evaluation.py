# orchestrator/api/routes/evaluation.py

from domain.errors import DomainError, ValidationFailed
from domain.evaluation import (
    evaluate_projects,
    get_groundtruth_qal,
    list_project_names,
)
from domain.models.evaluation import EvaluateProjectsCommand
from flask import request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation import EvaluateProjectsRequest, OkResponseAny


def _extract_token(req) -> str | None:
    # Preferred: Authorization: Bearer <token>
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.removeprefix("Bearer ").strip()

    # Legacy fallback: token in JSON body
    payload = req.get_json(silent=True) or {}
    return payload.get("token")


def register(app, ok, spec):
    # New standard endpoint

    @app.route("/evaluate-ai/projects", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=OkResponseAny,
            HTTP_400=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluate_ai_projects():
        token = _extract_token(request)

        if not token:
            raise DomainError(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        return ok(lambda: list_project_names(token))

    # Internal frontend helper endpoint.
    # No user input. Deterministic state check for groundtruth set existence.
    # Not part of public API contract.

    @app.route("/groundtruth_qal", methods=["GET"])
    def groundtruth_qal():
        return ok(get_groundtruth_qal)

    @app.route("/evaluate-ai", methods=["POST"])
    @spec.validate(
        body=Request(EvaluateProjectsRequest),
        resp=Response(
            HTTP_200=OkResponseAny,
            HTTP_400=ErrorResponse,  # invalid payload
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["evaluation"],
    )
    def evaluate_ai():
        payload = request.get_json(silent=True) or {}
        token = _extract_token(request)

        try:
            contract = EvaluateProjectsRequest.model_validate(payload)
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid request payload.",
                meta={"details": e.errors()},
            )

        if not token:
            raise DomainError(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        cmd = EvaluateProjectsCommand.from_contract(contract, token)
        return ok(lambda: evaluate_projects(cmd))
