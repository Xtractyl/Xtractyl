# orchestrator/api/routes/evaluation.py

from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.evaluation import (
    evaluate_projects,
    get_groundtruth_qal,
    list_project_names,
)
from domain.models.evaluation import EvaluateProjectsCommand
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError as PydanticValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation import (
    EvaluateProjectsRequest,
    EvaluateProjectsResponse,
    ProjectNamesResponse,
)
from api.utils.auth import extract_token


def register(app, spec):
    # New standard endpoint

    @app.route("/evaluate-ai/projects", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ProjectNamesResponse,
            HTTP_400=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluate_ai_projects():
        token = extract_token(request)

        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        result = list_project_names(token)
        return jsonify(result), 200

    # Internal frontend helper endpoint.
    # No user input. Deterministic state check for groundtruth set existence.
    # Not part of public API contract.

    @app.route("/groundtruth_qal", methods=["GET"])
    def groundtruth_qal():
        result = get_groundtruth_qal()
        return jsonify(result), 200

    @app.route("/evaluate-ai", methods=["POST"])
    @spec.validate(
        body=Request(EvaluateProjectsRequest),
        resp=Response(
            HTTP_200=EvaluateProjectsResponse,
            HTTP_400=ErrorResponse,  # invalid payload
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["evaluation"],
    )
    def evaluate_ai():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        try:
            contract = EvaluateProjectsRequest.model_validate(payload)
        except PydanticValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid request payload.",
                meta={"details": e.errors()},
            )

        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        cmd = EvaluateProjectsCommand.from_contract(
            groundtruth_project=contract.groundtruth_project,
            comparison_project=contract.comparison_project,
            token=token,
        )
        result = evaluate_projects(cmd)
        try:
            validated = EvaluateProjectsResponse.model_validate(result)
        except PydanticValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )

        return jsonify(validated.model_dump()), 200
