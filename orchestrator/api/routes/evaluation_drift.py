# orchestrator/api/routes/evaluation_drift.py

from domain.errors import ValidationFailed
from domain.evaluation_drift import get_evaluation_drift
from domain.models.evaluation_drift import GetEvaluationDriftCommand
from flask import request
from flask_pydantic_spec import Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation_drift import GetEvaluationDriftRequest, OkResponseAny


def register(app, ok, spec):
    @app.route("/evaluation-drift", methods=["GET"])
    @spec.validate(
        query=GetEvaluationDriftRequest,
        resp=Response(
            HTTP_200=OkResponseAny,
            HTTP_400=ErrorResponse,  # invalid query params
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

        cmd = GetEvaluationDriftCommand.from_contract(contract.model_dump())

        return ok(lambda: get_evaluation_drift(cmd))
