# orchestrator/api/routes/evaluation.py

from domain.evaluation import (
    evaluate_projects,
    get_groundtruth_qal,
    list_project_names,
)
from domain.models.evaluation import EvaluateProjectsCommand
from flask import request
from pydantic import ValidationError

from api.contracts.evaluation import EvaluateProjectsRequest


def _extract_token(req) -> str | None:
    # Preferred: Authorization: Bearer <token>
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.removeprefix("Bearer ").strip()

    # Legacy fallback: token in JSON body
    payload = req.get_json(silent=True) or {}
    return payload.get("token")


def register(app, ok):
    @app.route("/evaluate-ai/projects", methods=["GET"])
    def evaluate_ai_projects():
        token = _extract_token(request)

        if not token:
            return ok(lambda: {"status": "error", "error": "token is required"})

        return ok(lambda: list_project_names(token))

    @app.route("/groundtruth_qal", methods=["GET"])
    def groundtruth_qal():
        return ok(get_groundtruth_qal)

    @app.route("/evaluate-ai", methods=["POST"])
    def evaluate_ai():
        payload = request.get_json(silent=True) or {}
        token = _extract_token(request)

        try:
            contract = EvaluateProjectsRequest.model_validate(payload)
        except ValidationError as e:
            errors = e.errors()
            return ok(
                lambda: {
                    "status": "error",
                    "error": "validation_error",
                    "details": errors,
                }
            )

        if not token:
            return ok(lambda: {"status": "error", "error": "token is required"})

        cmd = EvaluateProjectsCommand.from_contract(contract, token)
        return ok(lambda: evaluate_projects(cmd))
