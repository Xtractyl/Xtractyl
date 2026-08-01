# orchestrator/api/routes/evaluation.py

from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.evaluation import (
    get_comparison_view,
    get_compatible_groundtruth_sets,
    get_evaluation,
    get_groundtruth_qals,
    list_evaluated_projects,
    list_project_names,
    save_as_gt_set,
)
from domain.models.evaluation import (
    CompatibleGroundtruthSetsCommand,
    EvaluateProjectsCommand,
    ProjectNameCommand,
    SaveAsGtSetCommand,
)
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from infrastructure.repository.evaluation_repository import EvaluationRepository
from infrastructure.repository.model_repository import ModelRepository
from infrastructure.repository.prelabelling_run_repository import PrelabellingRunRepository
from infrastructure.repository.project_repository import ProjectRepository
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.evaluation import (
    CompatibleGroundtruthSetsRequest,
    CompatibleGroundtruthSetsResponse,
    EvaluateProjectsRequest,
    EvaluateProjectsResponse,
    GetComparisonViewRequest,
    GetComparisonViewResponse,
    GroundtruthQalsResponse,
    ListEvaluatedProjectsResponse,
    ProjectNamesResponse,
    SaveAsGtSetRequest,
    SaveAsGtSetResponse,
)
from api.utils.auth import extract_token


def register(app, spec, session_factory=None):
    @app.route("/evaluate-ai/projects", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ProjectNamesResponse,
            HTTP_401=ErrorResponse,  # missing token
            HTTP_502=ErrorResponse,  # label studio unreachable
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluate_ai_projects():
        token = extract_token(request)

        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        result = list_project_names(token)
        return jsonify(result), 200

    @app.route("/groundtruth_qals", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=GroundtruthQalsResponse,
            HTTP_404=ErrorResponse,  # no groundtruth sets found
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def groundtruth_qals():
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            result = get_groundtruth_qals(project_repo=project_repo)
        finally:
            db.close()
        try:
            validated = GroundtruthQalsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/groundtruth_qals/compatible", methods=["POST"])
    @spec.validate(
        body=Request(CompatibleGroundtruthSetsRequest),
        resp=Response(
            HTTP_200=CompatibleGroundtruthSetsResponse,
            HTTP_404=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def compatible_groundtruth_sets():
        contract = CompatibleGroundtruthSetsRequest.model_validate(
            request.get_json(silent=True) or {}
        )
        cmd = CompatibleGroundtruthSetsCommand.from_contract(
            comparison_project=contract.comparison_project
        )
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            result = get_compatible_groundtruth_sets(
                cmd.comparison_project, project_repo=project_repo, run_repo=run_repo
            )
        finally:
            db.close()
        try:
            validated = CompatibleGroundtruthSetsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/evaluate-ai", methods=["POST"])
    @spec.validate(
        body=Request(EvaluateProjectsRequest),
        resp=Response(
            HTTP_200=EvaluateProjectsResponse,
            HTTP_401=ErrorResponse,  # missing token
            HTTP_404=ErrorResponse,  # project not found
            HTTP_409=ErrorResponse,  # filename or label mismatch
            HTTP_502=ErrorResponse,  # label studio unreachable
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluate_ai():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        contract = EvaluateProjectsRequest.model_validate(payload)
        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        cmd = EvaluateProjectsCommand.from_contract(
            groundtruth_project=contract.groundtruth_project,
            comparison_project=contract.comparison_project,
            token=token,
        )
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            eval_repo = EvaluationRepository(db)
            model_repo = ModelRepository(db)
            # Pure read now: sync_missing_evaluations (called internally
            # after a run finishes or a GT set is created) is the only
            # place evaluations get created — this endpoint no longer
            # computes on demand. A 404 here for a 'done' run with a
            # matching groundtruth set would indicate a sync bug, not
            # something for the caller to trigger by asking again.
            result = get_evaluation(
                cmd.groundtruth_project,
                cmd.comparison_project,
                project_repo=project_repo,
                run_repo=run_repo,
                eval_repo=eval_repo,
                model_repo=model_repo,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = EvaluateProjectsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )

        return jsonify(validated.model_dump()), 200

    @app.route("/save-as-gt-set", methods=["POST"])
    @spec.validate(
        body=Request(SaveAsGtSetRequest),
        resp=Response(
            HTTP_200=SaveAsGtSetResponse,
            HTTP_401=ErrorResponse,
            HTTP_404=ErrorResponse,
            HTTP_409=ErrorResponse,
            HTTP_500=ErrorResponse,
            HTTP_502=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def save_as_gt_set_route():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )

        contract = SaveAsGtSetRequest.model_validate(payload)
        cmd = SaveAsGtSetCommand.from_contract(
            source_project=contract.source_project,
            token=token,
        )
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            eval_repo = EvaluationRepository(db)
            result = save_as_gt_set(
                cmd, project_repo=project_repo, run_repo=run_repo, eval_repo=eval_repo
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = SaveAsGtSetResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/evaluations/comparison", methods=["GET"])
    @spec.validate(
        query=GetComparisonViewRequest,
        resp=Response(
            HTTP_200=GetComparisonViewResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["evaluation"],
    )
    def evaluations_comparison():
        try:
            contract = GetComparisonViewRequest.model_validate(dict(request.args or {}))
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        cmd = ProjectNameCommand.from_contract(contract.project_name)
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            model_repo = ModelRepository(db)
            eval_repo = EvaluationRepository(db)
            result = get_comparison_view(
                cmd.project_name,
                project_repo=project_repo,
                run_repo=run_repo,
                model_repo=model_repo,
                eval_repo=eval_repo,
            )
        finally:
            db.close()
        try:
            validated = GetComparisonViewResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/evaluations/projects", methods=["GET"])
    @spec.validate(
        resp=Response(HTTP_200=ListEvaluatedProjectsResponse, HTTP_500=ErrorResponse),
        tags=["evaluation"],
    )
    def evaluations_projects():
        db = session_factory()
        try:
            project_repo = ProjectRepository(db)
            run_repo = PrelabellingRunRepository(db)
            eval_repo = EvaluationRepository(db)
            projects = list_evaluated_projects(
                project_repo=project_repo, run_repo=run_repo, eval_repo=eval_repo
            )
        finally:
            db.close()
        try:
            validated = ListEvaluatedProjectsResponse.model_validate({"projects": projects})
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
