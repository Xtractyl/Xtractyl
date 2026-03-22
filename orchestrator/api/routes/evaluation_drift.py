# orchestrator/api/routes/evaluation_drift.py

from domain.errors import InternalError, ValidationFailed
from domain.evaluation_drift import get_evaluation_drift
from domain.models.evaluation_drift import GetEvaluationDriftCommand
from flask import jsonify, request
from flask_pydantic_spec import Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation_drift import GetEvaluationDriftRequest, GetEvaluationDriftResponse


def register(app, spec):
    @app.route("/evaluation-drift", methods=["GET"])
    @spec.validate(
        query=GetEvaluationDriftRequest,
        resp=Response(
            HTTP_200=GetEvaluationDriftResponse,
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["evaluation-drift"],
    )
    def evaluation_drift():
        payload = dict(request.args or {})

        try:
            contract = GetEvaluationDriftRequest.model_validate(payload)
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        # GetEvaluationDriftCommand gets a dict by .model_dump as expected
        # but it currently just requires any argument as it currently does not use it
        cmd = GetEvaluationDriftCommand.from_contract(contract.model_dump())
        result = get_evaluation_drift(cmd)
        try:
            validated = GetEvaluationDriftResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
