# orchestrator/api/routes/evaluation_drift.py

from domain.evaluation_drift import get_evaluation_drift
from domain.models.evaluation_drift import GetEvaluationDriftCommand
from flask import request
from pydantic import ValidationError

from api.contracts.evaluation_drift import GetEvaluationDriftRequest


def register(app, ok):
    @app.route("/evaluation-drift", methods=["GET"])
    def evaluation_drift():
        payload = dict(request.args or {})

        try:
            contract = GetEvaluationDriftRequest.model_validate(payload)
        except ValidationError as e:
            return {
                "status": "error",
                "error": "validation_error",
                "details": e.errors(),
            }

        cmd = GetEvaluationDriftCommand.from_contract(contract)

        return ok(lambda: get_evaluation_drift(cmd))
