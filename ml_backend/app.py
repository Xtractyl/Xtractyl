# ml_backend/app.py
import os

from api.error_handler import register_error_handlers
from api.routes import register_routes
from flask import Flask
from flask_pydantic_spec import FlaskPydanticSpec
from utils.logging_utils import dev_logger, safe_logger

safe_logger.info("ml_backend_starting")
if dev_logger:
    dev_logger.info("dev_logging_enabled")


APP_PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))


def create_app() -> Flask:
    app = Flask(__name__)
    spec = FlaskPydanticSpec("flask", title="ML Backend API", version="v1", path="apidoc")
    register_routes(app, spec)
    register_error_handlers(
        app=app,
        logger_safe=safe_logger,
        logger_dev=dev_logger,
    )
    spec.register(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
