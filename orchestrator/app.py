# orchestrator/app.py
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from routes.check_project_exists import check_project_exists
from routes.create_project import create_project_main_from_payload
from routes.get_results_table import build_results_table

# async helpers (no blueprint)
from routes.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_logs_since,
    get_job_status,
)
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

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN", f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"
)
APP_PORT = int(os.getenv("ORCH_PORT", "5001"))

app = Flask(__name__)
CORS(app, origins=[FRONTEND_ORIGIN])


def ok(fn):
    try:
        data = fn()
        return jsonify({"status": "success", "logs": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


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


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


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
    limit = int(payload.get("limit", 50))
    offset = int(payload.get("offset", 0))

    def run():
        if not project_name or not token:
            raise ValueError("project_name and token are required")
        return build_results_table(token, project_name, limit=limit, offset=offset)

    return ok(run)


# ---------- async job endpoints (no blueprint) ----------


@app.route("/prelabel_project_async", methods=["POST"])
def route_enqueue_job():
    payload = request.get_json() or {}
    return ok(lambda: enqueue_prelabel_job(payload))


@app.route("/jobs/<job_id>", methods=["GET"])
def route_job_status(job_id):
    return ok(lambda: get_job_status(job_id))


@app.route("/jobs/<job_id>/logs", methods=["GET"])
def route_job_logs(job_id):
    try:
        start = int(request.args.get("from", "0"))
    except ValueError:
        start = 0
    return ok(lambda: get_job_logs_since(job_id, start))


@app.route("/prelabel_project", methods=["POST"])
def prelabel_project():
    payload = request.get_json() or {}
    return ok(lambda: enqueue_prelabel_job(payload))


@app.route("/prelabel/status/<job_id>", methods=["GET"])
def compat_status(job_id):
    return ok(lambda: get_job_status(job_id))


@app.route("/prelabel/logs/<job_id>", methods=["GET"])
def compat_logs(job_id):
    try:
        start = int(request.args.get("from", "0"))
    except ValueError:
        start = 0
    return ok(lambda: get_job_logs_since(job_id, start))


@app.route("/prelabel/cancel/<job_id>", methods=["POST"])
def compat_cancel(job_id):
    return ok(lambda: cancel_prelabel_job(job_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
