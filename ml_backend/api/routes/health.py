# ml_backend/api/routes/health.py
from flask import Flask, jsonify
from flask_pydantic_spec import FlaskPydanticSpec, Response

from api.contracts.health import HealthResponse


def register(app: Flask, spec: FlaskPydanticSpec) -> None:
    @app.route("/health", methods=["GET"])
    @spec.validate(
        resp=Response(HTTP_200=HealthResponse),
        tags=["system"],
    )
    def health():
        return jsonify({"status": "ok"}), 200

# /setup is required by Label Studio for ML backend registration
    @app.route("/setup", methods=["GET", "POST"])
    @spec.validate(
        resp=Response(HTTP_200=HealthResponse),
        tags=["system"],
    )
    def setup():
        return jsonify({"status": "ok"}), 200
