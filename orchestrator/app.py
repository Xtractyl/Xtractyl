# orchestrator/app.py
import os
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS
from routes.check_project_exists import check_project_exists
from routes.create_project import create_project_main_from_payload
from routes.get_results_table import build_results_table

from routes.list_html_folders import list_html_subfolders
from routes.load_ollama_models import (
    load_ollama_models_main_wrapper as load_ollama_models_main,
)
from routes.questions_and_labels import (
    list_projects_route,
    list_qal_jsons_route,
    preview_qal_route,
)
from routes.upload_tasks import upload_tasks_main_from_payload

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

# -------------------------------------------------------------------
# Keep existing @app.route(...) endpoints BELOW THIS LINE for now.
# XC-138 will move them into orchestrator/api/routes/*.py
# -------------------------------------------------------------------


# ---------- sync endpoints (unchanged) ----------


@app.route("/create_project", methods=["POST"])
def create_project():
    payload = request.get_json()
    return ok(lambda: create_project_main_from_payload(payload))


@app.route("/load_models", methods=["POST"])
def load_models():
    return ok(load_ollama_models_main)


@app.route("/upload_tasks", methods=["POST"])
def upload_tasks():
    payload = request.get_json()
    return ok(lambda: upload_tasks_main_from_payload(payload))


@app.route("/project_exists", methods=["POST"])
def project_exists():
    return check_project_exists()


@app.route("/list_html_subfolders", methods=["GET"])
def list_html_subfolders_route():
    return list_html_subfolders()


@app.route("/list_projects", methods=["GET"])
def list_projects():
    return list_projects_route()


@app.route("/list_qal_jsons", methods=["GET"])
def list_qal_jsons():
    return list_qal_jsons_route()


@app.route("/preview_qal", methods=["GET"])
def preview_qal():
    return preview_qal_route()


@app.route("/get_results_table", methods=["POST"])
def get_results_table_route():
    payload = request.get_json() or {}
    project_name = payload.get("project_name")
    token = payload.get("token")

    def run():
        if not project_name or not token:
            raise ValueError("project_name and token are required")
        return build_results_table(token, project_name)

    return ok(run)



