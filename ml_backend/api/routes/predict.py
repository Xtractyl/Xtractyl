# ml_backend/api/routes/predict.py
from domain.errors import InternalError, ValidationFailed
from domain.models.predict import PredictCommand
from domain.predict import run_predict
from flask import Flask, jsonify, request
from flask_pydantic_spec import FlaskPydanticSpec, Request, Response
from pydantic import ValidationError

from api.contracts.errors import ErrorResponse
from api.contracts.predict import PredictRequest, PredictResponse


def register(app: Flask, spec: FlaskPydanticSpec) -> None:
    @app.route("/predict", methods=["POST"])
    @spec.validate(
        body=Request(PredictRequest),
        resp=Response(
            HTTP_200=PredictResponse,
            HTTP_422=ErrorResponse,  # contract violation
            HTTP_502=ErrorResponse,  # label studio unreachable
            HTTP_500=ErrorResponse,  # unexpected
        ),
        tags=["predict"],
    )
    def predict():
        try:
            contract = PredictRequest.model_validate(request.get_json(silent=True) or {})
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_REQUEST",
                message="Request did not match expected schema.",
                details=e.errors(),
            )

        cmd = PredictCommand.from_contract(contract)
        result = run_predict(cmd)

        try:
            validated = PredictResponse.model_validate(result)
        except ValidationError as e:
            raise InternalError(
                code="RESPONSE_CONTRACT_VIOLATED",
                message="Internal response did not match expected schema.",
                meta={"details": e.errors()},
            )

        return jsonify(validated.model_dump()), 200
