# orchestrator/api/routes/results.py

from flask import request
from pydantic import ValidationError

from api.contracts.results import GetResultsTableRequest
from api.domain.results import build_results_table


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

        return ok(lambda: build_results_table(token, contract.project_name))
