# orchestrator/api/routes/results.py

from domain.errors import InternalError, ValidationFailed
from domain.models.results import GetResultsTableCommand
from domain.results import build_results_table, list_projects_ready_for_results
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from infrastructure.repository.prelabelling_run_repository import PrelabellingRunRepository
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.results import (
    GetResultsTableRequest,
    GetResultsTableResponse,
    ListProjectsReadyForResultsResponse,
)


def register(app, spec, session_factory=None):
    @app.route("/list_projects_ready_for_results", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ListProjectsReadyForResultsResponse,
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["results"],
    )
    def list_projects_ready_for_results_route():
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            result = list_projects_ready_for_results(run_repo=run_repo)
        finally:
            db.close()
        try:
            validated = ListProjectsReadyForResultsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/results/table", methods=["POST"])
    @spec.validate(
        body=Request(GetResultsTableRequest),
        resp=Response(
            HTTP_200=GetResultsTableResponse,
            HTTP_404=ErrorResponse,  # project not found
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["results"],
    )
    def results_table_route():
        payload = request.get_json(silent=True) or {}

        try:
            contract = GetResultsTableRequest.model_validate(payload)
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid request payload.",
                meta={"details": e.errors()},
            )

        cmd = GetResultsTableCommand.from_contract(
            project_name=contract.project_name,
        )

        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            result = build_results_table(cmd, run_repo=run_repo)
        finally:
            db.close()
        try:
            validated = GetResultsTableResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
