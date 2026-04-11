# orchestrator/api/routes/projects.py
from domain.errors import InternalError, Unauthorized, ValidationFailed
from domain.models.projects import (
    CreateProjectCommand,
    ListQalJsonsCommand,
    PreviewQalCommand,
    ProjectExistsCommand,
    UploadTasksCommand,
)
from domain.projects import (
    check_project_exists,
    create_project_main_from_payload,
    list_html_subfolders,
    list_qal_jsons,
    upload_tasks_main_from_payload,
)
from domain.projects import (
    preview_qal as domain_preview_qal,
)
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ListHtmlSubfoldersResponse,
    ListQalJsonsRequest,
    ListQalJsonsResponse,
    PreviewQalRequest,
    PreviewQalResponse,
    ProjectExistsRequest,
    ProjectExistsResponse,
    UploadTasksRequest,
    UploadTasksResponse,
)
from api.utils.auth import extract_token


def register(app, ok, spec):
    @app.route("/create_project", methods=["POST"])
    @spec.validate(
        body=Request(CreateProjectRequest),
        resp=Response(
            HTTP_200=CreateProjectResponse,
            HTTP_401=ErrorResponse,  # missing token
            HTTP_502=ErrorResponse,  # label studio or ml backend unreachable
            HTTP_500=ErrorResponse,
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
    @spec.validate(
        body=Request(UploadTasksRequest),
        resp=Response(
            HTTP_200=UploadTasksResponse,
            HTTP_400=ErrorResponse,  # invalid path
            HTTP_401=ErrorResponse,
            HTTP_404=ErrorResponse,  # file not found
            HTTP_500=ErrorResponse,  # unexpected global exception handler
            HTTP_502=ErrorResponse,
        ),
        tags=["projects"],
    )
    def upload_tasks_route():
        token = extract_token(request)
        if not token:
            raise Unauthorized(
                code="TOKEN_REQUIRED",
                message="Authorization token is required.",
            )
        try:
            contract = UploadTasksRequest.model_validate(request.get_json(silent=True) or {})
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        cmd = UploadTasksCommand.from_contract(
            project=contract.project, html_folder=contract.html_folder, token=token
        )
        result = upload_tasks_main_from_payload(cmd)
        try:
            validated = UploadTasksResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/project_exists", methods=["POST"])
    @spec.validate(
        body=Request(ProjectExistsRequest),
        resp=Response(
            HTTP_200=ProjectExistsResponse,
            HTTP_409=ErrorResponse,  # project already exists
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["projects"],
    )
    def project_exists_route():
        try:
            contract = ProjectExistsRequest.model_validate(request.get_json(silent=True) or {})
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        cmd = ProjectExistsCommand.from_contract(project=contract.project)
        result = check_project_exists(cmd)
        try:
            validated = ProjectExistsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

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
    @spec.validate(
        query=ListQalJsonsRequest,
        resp=Response(
            HTTP_200=ListQalJsonsResponse,
            HTTP_400=ErrorResponse,  # invalid path
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["projects"],
    )
    def list_qal_jsons_route():
        try:
            contract = ListQalJsonsRequest.model_validate(dict(request.args))
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        cmd = ListQalJsonsCommand.from_contract(project=contract.project)
        result = list_qal_jsons(cmd)
        try:
            validated = ListQalJsonsResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/preview_qal", methods=["GET"])
    @spec.validate(
        query=PreviewQalRequest,
        resp=Response(
            HTTP_200=PreviewQalResponse,
            HTTP_400=ErrorResponse,  # invalid path
            HTTP_404=ErrorResponse,  # file not found
            HTTP_500=ErrorResponse,  # unexpected global exception handler
        ),
        tags=["projects"],
    )
    def preview_qal():
        try:
            contract = PreviewQalRequest.model_validate(dict(request.args))
        except ValidationError as e:
            raise ValidationFailed(
                code="VALIDATION_FAILED",
                message="Invalid query parameters.",
                meta={"details": e.errors()},
            )
        cmd = PreviewQalCommand.from_contract(project=contract.project, filename=contract.filename)
        result = domain_preview_qal(cmd)
        try:
            validated = PreviewQalResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200
