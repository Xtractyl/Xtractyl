# orchestrator/api/routes/results.py

from domain.errors import Unauthorized, ValidationFailed
from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.results import GetResultsTableRequest, GetResultsTableResponse
from api.utils.auth import extract_token


def register(app, spec):
    # New standard endpoint
    @app.route("/results/table", methods=["POST"])
    @spec.validate(
        body=Request(GetResultsTableRequest),
        resp=Response(
            HTTP_200=GetResultsTableResponse,
            HTTP_400=ErrorResponse,  # invalid payload
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["results"],
    )
    def results_table_route():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        try:
            contract = GetResultsTableRequest.model_validate(payload)
        except ValidationError as e:
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

        cmd = GetResultsTableCommand.from_contract(
            project_name=contract.project_name,
            token=token,
        )

        result = build_results_table(cmd)
        return jsonify(result), 200
