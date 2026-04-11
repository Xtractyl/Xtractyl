# orchestrator/api/routes/evaluation.py

from domain.errors import InternalError, Unauthorized
from domain.evaluation import (
    evaluate_projects,
    get_groundtruth_qals,
    list_project_names,
    save_as_gt_set,
)
from domain.models.evaluation import EvaluateProjectsCommand, SaveAsGtSetCommand
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError as PydanticValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation import (
    EvaluateProjectsRequest,
    EvaluateProjectsResponse,
    ProjectNamesResponse,
    SaveAsGtSetRequest,
    SaveAsGtSetResponse,
)
from api.utils.auth import extract_token


def register(app, spec):
    # New standard endpoint

    @app.route("/evaluate-ai/projects", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ProjectNamesResponse,
            HTTP_401=ErrorResponse,  # missing token
            HTTP_502=ErrorResponse,  # label studio unreachable
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

    @app.route("/groundtruth_qals", methods=["GET"])
    def groundtruth_qals():
        result = get_groundtruth_qals()
        return jsonify(result), 200

    @app.route("/evaluate-ai", methods=["POST"])
    @spec.validate(
        body=Request(EvaluateProjectsRequest),
        resp=Response(
            HTTP_200=EvaluateProjectsResponse,
            HTTP_401=ErrorResponse,  # missing token
            HTTP_404=ErrorResponse,  # project not found
            HTTP_409=ErrorResponse,  # filename or label mismatch
            HTTP_502=ErrorResponse,  # label studio unreachable
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluate_ai():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        contract = EvaluateProjectsRequest.model_validate(payload)
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

    @app.route("/save-as-gt-set", methods=["POST"])
    @spec.validate(
        body=Request(SaveAsGtSetRequest),
        resp=Response(
            HTTP_200=SaveAsGtSetResponse,
            HTTP_401=ErrorResponse,
            HTTP_404=ErrorResponse,
            HTTP_409=ErrorResponse,
            HTTP_500=ErrorResponse,
            HTTP_502=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def save_as_gt_set_route():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )

        contract = SaveAsGtSetRequest.model_validate(payload)
        cmd = SaveAsGtSetCommand.from_contract(
            source_project=contract.source_project,
            gt_set_name=contract.gt_set_name,
            token=token,
        )
        result = save_as_gt_set(cmd)
        try:
            validated = SaveAsGtSetResponse.model_validate(result)
        except PydanticValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
