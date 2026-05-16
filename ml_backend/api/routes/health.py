# ml_backend/api/routes/health.py
from api.contracts.health import HealthResponse
from flask import Flask, jsonify
from flask_pydantic_spec import FlaskPydanticSpec, Response


def register(app: Flask, spec: FlaskPydanticSpec) -> None:
    @app.route("/health", methods=["GET"])
    @spec.validate(
        resp=Response(HTTP_200=HealthResponse),
        tags=["system"],
    )
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/setup", methods=["GET", "POST"])
    @spec.validate(
        resp=Response(HTTP_200=HealthResponse),
        tags=["system"],
    )
    def setup():
        return jsonify({"status": "ok"}), 200
