# orchestrator/api/routes/jobs.py
from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_status,
)
from domain.models.jobs import CancelJobCommand, EnqueueJobCommand, JobStatusCommand
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.jobs import (
    CancelJobResponse,
    EnqueueJobRequest,
    EnqueueJobResponse,
    JobStatusRequest,
    JobStatusResponse,
)
from api.utils.auth import extract_token


def register(app, spec):
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
        result = get_job_status(cmd)
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
        result = enqueue_prelabel_job(cmd)
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
        result = cancel_prelabel_job(cmd)
        try:
            validated = CancelJobResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
