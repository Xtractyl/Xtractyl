# ml_backend/api/routes/__init__.py
from api.routes import health, predict
from flask import Flask
from flask_pydantic_spec import FlaskPydanticSpec


def register_routes(app: Flask, spec: FlaskPydanticSpec) -> None:
    health.register(app, spec)
    predict.register(app, spec)
