# orchestrator/api/routes/jobs.py
from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_status,
    handle_job_failed,
    handle_task_result,
)
from domain.models.jobs import (
    CancelJobCommand,
    EnqueueJobCommand,
    JobFailedCommand,
    JobStatusCommand,
    TaskResultCommand,
)
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from infrastructure.repository.evaluation_repository import EvaluationRepository
from infrastructure.repository.model_repository import ModelRepository
from infrastructure.repository.prelabelling_run_repository import PrelabellingRunRepository
from infrastructure.repository.project_repository import ProjectRepository
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.jobs import (
    CancelJobResponse,
    EnqueueJobRequest,
    EnqueueJobResponse,
    JobFailedRequest,
    JobFailedResponse,
    JobStatusRequest,
    JobStatusResponse,
    TaskResultRequest,
    TaskResultResponse,
)
from api.utils.auth import extract_token


def register(app, spec, session_factory):
    @app.route("/prelabel/status/<job_id>", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=JobStatusResponse,
            HTTP_400=ErrorResponse,  # invalid job_id
            HTTP_500=ErrorResponse,
        ),
        tags=["jobs"],
    )
    def prelabel_status_route(job_id):
        try:
            contract = JobStatusRequest.model_validate({"job_id": job_id})
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid job_id.",
                meta={"details": e.errors()},
            )
        cmd = JobStatusCommand.from_contract(job_id=contract.job_id)
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            result = get_job_status(cmd, run_repo=run_repo)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        try:
            validated = JobStatusResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/prelabel_project", methods=["POST"])
    @spec.validate(
        body=Request(EnqueueJobRequest),
        resp=Response(
            HTTP_200=EnqueueJobResponse,
            HTTP_400=ErrorResponse,  # validation failed
            HTTP_401=ErrorResponse,  # missing token
            HTTP_409=ErrorResponse,  # a prelabelling run already exists for this project
            HTTP_500=ErrorResponse,
        ),
        tags=["jobs"],
    )
    def prelabel_project():
        token = extract_token(request)
        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        contract = EnqueueJobRequest.model_validate(request.get_json(silent=True) or {})
        cmd = EnqueueJobCommand.from_contract(contract=contract, token=token)
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            project_repo = ProjectRepository(db)
            model_repo = ModelRepository(db)
            result = enqueue_prelabel_job(
                cmd, run_repo=run_repo, project_repo=project_repo, model_repo=model_repo
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = EnqueueJobResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/prelabel/cancel/<job_id>", methods=["POST"])
    @spec.validate(
        resp=Response(
            HTTP_200=CancelJobResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["jobs"],
    )
    def prelabel_cancel_route(job_id):
        cmd = CancelJobCommand.from_contract(job_id=job_id)
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            result = cancel_prelabel_job(cmd, run_repo=run_repo)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = CancelJobResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/prelabel/job-failed", methods=["POST"])
    @spec.validate(
        body=Request(JobFailedRequest),
        resp=Response(
            HTTP_200=JobFailedResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["jobs"],
    )
    def prelabel_job_failed():
        contract = JobFailedRequest.model_validate(request.get_json(silent=True) or {})
        cmd = JobFailedCommand.from_contract(contract)
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            result = handle_job_failed(cmd, run_repo=run_repo)

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = JobFailedResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/prelabel/task-result", methods=["POST"])
    @spec.validate(
        body=Request(TaskResultRequest),
        resp=Response(
            HTTP_200=TaskResultResponse,
            HTTP_404=ErrorResponse,  # run or run task not found
            HTTP_409=ErrorResponse,  # label or html-hash mismatch (via sync_missing_evaluations)
            HTTP_500=ErrorResponse,
        ),
        tags=["jobs"],
    )
    def prelabel_task_result():
        contract = TaskResultRequest.model_validate(request.get_json(silent=True) or {})
        cmd = TaskResultCommand.from_contract(contract)
        db = session_factory()
        try:
            run_repo = PrelabellingRunRepository(db)
            project_repo = ProjectRepository(db)
            eval_repo = EvaluationRepository(db)
            result = handle_task_result(
                cmd, run_repo=run_repo, project_repo=project_repo, eval_repo=eval_repo
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = TaskResultResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump(by_alias=True)), 200
