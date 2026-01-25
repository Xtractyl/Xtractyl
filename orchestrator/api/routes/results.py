# orchestrator/api/routes/results.py

from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table
from flask import request
from pydantic import ValidationError

from api.contracts.results import GetResultsTableRequest


def _extract_token(req) -> str | None:
    # Preferred: Authorization: Bearer <token>
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.removeprefix("Bearer ").strip()

    # Legacy fallback: token in JSON body
    payload = req.get_json(silent=True) or {}
    return payload.get("token")


def register(app, ok):
    # New standard endpoint
    @app.route("/results/table", methods=["POST"])
    def results_table_route():
        payload = request.get_json(silent=True) or {}
        token = _extract_token(request)

        try:
            contract = GetResultsTableRequest.model_validate(payload)
        except ValidationError as e:
            raise ValueError(e.errors())

        if not token:
            raise ValueError("token is required")

        cmd = GetResultsTableCommand.from_contract(contract, token)

        return ok(lambda: build_results_table(cmd))
