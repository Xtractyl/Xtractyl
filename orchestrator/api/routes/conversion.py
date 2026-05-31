# orchestrator/api/routes/conversion.py

from domain.conversion import (
    get_conversion_status,
    handle_conversion_callback,
    prepare_conversion,
    start_conversion,
)
from domain.errors import InternalError
from domain.models.conversion import (
    ConversionCallbackCommand,
    ConversionStatusCommand,
    ConvertCommand,
    PrepareConversionCommand,
)
from flask import jsonify, request
from flask_pydantic_spec import Request, Response
from infrastructure.repository.conversion_repository import ConversionRepository
from pydantic import ValidationError

from api.contracts.conversion import (
    ConversionCallbackRequest,
    ConversionStatusResponse,
    ConvertRequest,
    ConvertResponse,
    PrepareConversionRequest,
    PrepareConversionResponse,
)
from api.contracts.errors import ErrorResponse


def register(app, spec, storage, queue, session_factory):
    @app.route("/conversion/prepare", methods=["POST"])
    @spec.validate(
        body=Request(PrepareConversionRequest),
        resp=Response(
            HTTP_200=PrepareConversionResponse,
            HTTP_409=ErrorResponse,
            HTTP_422=ErrorResponse,
            HTTP_502=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["conversion"],
    )
    def conversion_prepare():
        contract = PrepareConversionRequest.model_validate(request.get_json(silent=True) or {})
        cmd = PrepareConversionCommand.from_contract(
            project=contract.project, filenames=contract.filenames
        )
        db = session_factory()
        try:
            repo = ConversionRepository(db)
            result = prepare_conversion(cmd, storage=storage, repo=repo)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = PrepareConversionResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/conversion/convert", methods=["POST"])
    @spec.validate(
        body=Request(ConvertRequest),
        resp=Response(
            HTTP_200=ConvertResponse,
            HTTP_404=ErrorResponse,
            HTTP_409=ErrorResponse,
            HTTP_500=ErrorResponse,
        ),
        tags=["conversion"],
    )
    def conversion_convert():
        contract = ConvertRequest.model_validate(request.get_json(silent=True) or {})
        cmd = ConvertCommand.from_contract(job_id=contract.job_id)
        db = session_factory()
        try:
            repo = ConversionRepository(db)
            result = start_conversion(cmd, repo=repo, queue=queue)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        try:
            validated = ConvertResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/conversion/status/<int:job_id>", methods=["GET"])
    @spec.validate(
        resp=Response(
            HTTP_200=ConversionStatusResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse
        ),
        tags=["conversion"],
    )
    def conversion_status(job_id: int):
        cmd = ConversionStatusCommand.from_contract(job_id=job_id)
        db = session_factory()
        try:
            repo = ConversionRepository(db)
            result = get_conversion_status(cmd, repo=repo)
        finally:
            db.close()
        try:
            validated = ConversionStatusResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )
        return jsonify(validated.model_dump()), 200

    @app.route("/conversion/callback", methods=["POST"])
    @spec.validate(
        body=Request(ConversionCallbackRequest),
        resp=Response(HTTP_200=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse),
        tags=["conversion"],
    )
    def conversion_callback():
        contract = ConversionCallbackRequest.model_validate(request.get_json(silent=True) or {})
        cmd = ConversionCallbackCommand.from_contract(
            job_id=contract.job_id,
            filename=contract.filename,
            html_key=contract.html_key,
            success=contract.success,
            error=contract.error,
        )
        db = session_factory()
        try:
            repo = ConversionRepository(db)
            result = handle_conversion_callback(cmd, repo=repo)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return jsonify(result), 200
