# orchestrator/api/routes/evaluation_views.py

from domain.errors import InternalError, ValidationFailed
from domain.evaluation_views import get_drift_view, get_regression_view
from domain.models.evaluation import ProjectNameCommand
from flask import jsonify, request
from flask_pydantic_spec import Response
from infrastructure.repository.evaluation_repository import EvaluationRepository
from infrastructure.repository.model_repository import ModelRepository
from infrastructure.repository.prelabelling_run_repository import PrelabellingRunRepository
from infrastructure.repository.project_repository import ProjectRepository
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation_views import (
    GetDriftViewResponse,
    GetRegressionViewResponse,
    ProjectNameRequest,
)


def register(app, spec, session_factory=None):
    @app.route("/evaluations/regression", methods=["GET"])
    @spec.validate(
        query=ProjectNameRequest,
        resp=Response(HTTP_200=GetRegressionViewResponse, HTTP_500=ErrorResponse),
        tags=["evaluation-views"],
    )
    def evaluations_regression():
        cmd = _project_name_command_from_request()
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            model_repo = ModelRepository(db)
            eval_repo = EvaluationRepository(db)
            result = get_regression_view(
                cmd.project_name,
                project_repo=project_repo,
                run_repo=run_repo,
                model_repo=model_repo,
                eval_repo=eval_repo,
            )
        finally:
            db.close()
        try:
            validated = GetRegressionViewResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/evaluations/drift", methods=["GET"])
    @spec.validate(
        query=ProjectNameRequest,
        resp=Response(HTTP_200=GetDriftViewResponse, HTTP_500=ErrorResponse),
        tags=["evaluation-views"],
    )
    def evaluations_drift():
        cmd = _project_name_command_from_request()
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            model_repo = ModelRepository(db)
            eval_repo = EvaluationRepository(db)
            result = get_drift_view(
                cmd.project_name,
                project_repo=project_repo,
                run_repo=run_repo,
                model_repo=model_repo,
                eval_repo=eval_repo,
            )
        finally:
            db.close()
        try:
            validated = GetDriftViewResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    def _project_name_command_from_request() -> ProjectNameCommand:
        try:
            contract = ProjectNameRequest.model_validate(dict(request.args or {}))
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        return ProjectNameCommand.from_contract(contract.project_name)
