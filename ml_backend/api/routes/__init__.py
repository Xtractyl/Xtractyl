# ml_backend/api/routes/__init__.py
from flask import Flask
from flask_pydantic_spec import FlaskPydanticSpec

from api.routes import health, predict


def register_routes(app: Flask, spec: FlaskPydanticSpec) -> None:
    health.register(app, spec)
    predict.register(app, spec)
