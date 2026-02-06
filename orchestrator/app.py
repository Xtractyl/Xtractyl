# orchestrator/app.py
import os

from api.error_handler import register_error_handlers
from api.routes import register_routes
from flask import Flask, Response, jsonify
from flask_cors import CORS
from utils.logging_utils import dev_logger, safe_logger

safe_logger.info("orchestrator_starting")
if dev_logger:
    dev_logger.info("dev_logging_enabled")


FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN", f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"
)
APP_PORT = int(os.getenv("ORCH_PORT", "5001"))


def ok(fn):
    data = fn()

    # passthrough: (payload, status) oder (Response, status)
    if isinstance(data, tuple) and len(data) == 2:
        body, status = data
        if isinstance(body, Response):
            return body, status
        return jsonify(body), status

    # passthrough: Response direkt
    if isinstance(data, Response):
        return data

    # legacy passthrough: {"status": "..."}
    if isinstance(data, dict) and data.get("status") in ("success", "error", "ok"):
        st = data["status"]
        code = 200 if st in ("success", "ok") else 400
        return jsonify(data), code

    # default wrapper
    return jsonify({"status": "success", "data": data}), 200


def create_app() -> Flask:
    app = Flask(__name__)
    # CORS: keep browser frontend working (incl. Authorization header)
    CORS(app, origins=[FRONTEND_ORIGIN], allow_headers=["Content-Type", "Authorization"])

    register_routes(app, ok)
    register_error_handlers(
        app=app,
        logger_safe=safe_logger,
        logger_dev=dev_logger,
    )
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
