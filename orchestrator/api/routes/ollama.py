# orchestrator/api/routes/ollama.py

from domain.errors import InternalError, ValidationFailed
from domain.models.ollama import ListModelsCommand, PullModelCommand
from domain.ollama import list_models, pull_model
from flask import Response, jsonify, request, stream_with_context
from flask_pydantic_spec import Request
from flask_pydantic_spec import Response as SpecResponse
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.ollama import ListModelsResponse, PullModelRequest, PullModelResponse


def register(app, spec):
    @app.route("/ollama/models", methods=["GET"])
    @spec.validate(
        resp=SpecResponse(
            HTTP_200=ListModelsResponse,
            HTTP_502=ErrorResponse,  # ollama unreachable
            HTTP_500=ErrorResponse,
        ),
        tags=["ollama"],
    )
    def list_models_route():
        cmd = ListModelsCommand.from_contract()
        result = list_models(cmd)
        try:
            validated = ListModelsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/ollama/models/pull", methods=["POST"])
    @spec.validate(
        body=Request(PullModelRequest),
        resp=SpecResponse(
            HTTP_200=PullModelResponse,
            HTTP_502=ErrorResponse,  # ollama unreachable
            HTTP_500=ErrorResponse,
        ),
        tags=["ollama"],
    )
    def pull_model_route():
        payload = request.get_json(silent=True) or {}
        try:
            contract = PullModelRequest.model_validate(payload)
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid request payload.",
                meta={"details": e.errors()},
            )
        cmd = PullModelCommand.from_contract(model=contract.model)
        return Response(
            stream_with_context(pull_model(cmd)),
            content_type="application/x-ndjson",
        )
