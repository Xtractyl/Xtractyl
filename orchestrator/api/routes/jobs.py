# orchestrator/api/routes/jobs.py
from domain.errors import InternalError, ValidationFailed
from domain.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_status,
)
from domain.models.jobs import JobStatusCommand
from flask import jsonify, request
from flask_pydantic_spec import Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.jobs import (
    JobStatusRequest,
    JobStatusResponse,
)


def register(app, ok, spec):
    @app.route("/prelabel_project", methods=["POST"])
    def prelabel_project():
        payload = request.get_json() or {}
        return ok(lambda: enqueue_prelabel_job(payload))

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

    @app.route("/prelabel/cancel/<job_id>", methods=["POST"])
    def compat_cancel(job_id):
        return ok(lambda: cancel_prelabel_job(job_id))
