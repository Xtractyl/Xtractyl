# orchestrator/api/routes/projects.py
from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.models.projects import CreateProjectCommand
from domain.projects import (
    check_project_exists,
    create_project_main_from_payload,
    list_html_subfolders,
    list_qal_jsons_route,
    preview_qal_route,
    upload_tasks_main_from_payload,
)
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ListHtmlSubfoldersResponse,
)
from api.utils.auth import extract_token


def register(app, ok, spec):
    @app.route("/create_project", methods=["POST"])
    @spec.validate(
        body=Request(CreateProjectRequest),
        resp=Response(
            HTTP_200=CreateProjectResponse,
            HTTP_400=ErrorResponse,  # invalid payload
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["projects"],
    )
    def create_project():
        payload = request.get_json(silent=True) or {}
        token = extract_token(request)

        try:
            contract = CreateProjectRequest.model_validate(payload)
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

        cmd = CreateProjectCommand.from_contract(
            title=contract.title,
            questions=contract.questions,
            labels=contract.labels,
            token=token,
        )

        result = create_project_main_from_payload(cmd)
        try:
            validated = CreateProjectResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/upload_tasks", methods=["POST"])
    def upload_tasks():
        payload = request.get_json()
        token = extract_token(request)
        return ok(lambda: upload_tasks_main_from_payload(payload, token))

    @app.route("/project_exists", methods=["POST"])
    def project_exists():
        return check_project_exists()

    @app.route("/list_html_subfolders", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ListHtmlSubfoldersResponse,
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["projects"],
    )
    def list_html_subfolders_route():
        result = list_html_subfolders()
        try:
            validated = ListHtmlSubfoldersResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/list_qal_jsons", methods=["GET"])
    def list_qal_jsons():
        return list_qal_jsons_route()

    @app.route("/preview_qal", methods=["GET"])
    def preview_qal():
        return preview_qal_route()
