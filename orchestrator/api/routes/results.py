# orchestrator/api/routes/results.py

from domain.errors import DomainError, ValidationFailed
from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table
from flask import request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.results import GetResultsTableRequest, OkResponseAny


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
    @app.route("/results/table", methods=["POST"])
    @spec.validate(
        body=Request(GetResultsTableRequest),
        resp=Response(
            HTTP_200=OkResponseAny,  # required: must be a Pydantic BaseModel
            HTTP_400=ErrorResponse,
            HTTP_404=ErrorResponse,
            HTTP_409=ErrorResponse,
            HTTP_502=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["results"],
    )
    def results_table_route():
        payload = request.get_json(silent=True) or {}
        token = _extract_token(request)

        try:
            contract = GetResultsTableRequest.model_validate(payload)
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

        cmd = GetResultsTableCommand.from_contract(contract, token)

        return ok(lambda: build_results_table(cmd))
