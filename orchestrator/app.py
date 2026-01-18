# orchestrator/app.py
import os
import traceback

from flask import Flask, jsonify
from flask_cors import CORS

from orchestrator.api.routes import register_routes

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN", f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"
)
APP_PORT = int(os.getenv("ORCH_PORT", "5001"))


def ok(fn):
    try:
        data = fn()

        # already wrapped? then pass through
        if isinstance(data, dict) and data.get("status") in ("success", "error"):
            return jsonify(data), 200 if data["status"] == "success" else 400

        # default: old frontend contract
        return jsonify({"status": "success", "logs": data}), 200
        # expected errors (guards)
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400
        # unexpected errors (bugs)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "trace": traceback.format_exc()}), 500


def create_app() -> Flask:
    app = Flask(__name__)

    # CORS: keep browser frontend working
    CORS(app, origins=[FRONTEND_ORIGIN])

    register_routes(app, ok)
    return app


app = create_app()
