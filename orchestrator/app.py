"""
Xtractyl Orchestrator API
=========================

Flask application exposing orchestration endpoints used by the React frontend.
It wires HTTP routes to the underlying functions in `routes/*`.

Conventions
-----------
- All responses are JSON.
- Success wrapper: {"status": "success", "logs": <any>}
- Error wrapper:   {"status": "error", "error": "<message>"}
- CORS is limited to the configured frontend origin (see FRONTEND_ORIGIN).

HTTP Statuses
-------------
- 200: Request handled successfully (even if the "logs" describe partial issues).
- 202: Accepted; an async job was created (client should poll status).
- 4xx: Client error (missing fields, invalid input, not found).
- 5xx: Unhandled exception or upstream service error.

Endpoints (overview)
--------------------
Label Studio / pipeline orchestration:
- POST /accept_predictions          → Accept model predictions as final annotations.
- GET  /compare_predictions         → Compare predictions with human annotations.
- POST /create_project              → Create a Label Studio project + config.
- GET  /export_annotations          → Export merged/final annotations.
- POST /load_models                 → Ensure Ollama models are available.
- POST /upload_tasks                → Upload HTML tasks to a project.

Pre‑labeling (async job lifecycle):
- POST /prelabel/start              → Start pre‑labeling; returns {"job_id"} (202 Accepted).
- GET  /prelabel/status/<job_id>    → Current status JSON for that job (poll this).
- POST /prelabel/cancel/<job_id>    → Request cancellation for a running job.

Health / helpers:
- GET  /health                      → Liveness probe.
- POST /project_exists              → Check if a project exists by title.
- GET  /list_html_subfolders        → List available HTML subfolders on disk.

Questions & Labels (Q&L) files:
- GET  /list_projects               → List project directories under data/projects.
- GET  /list_qal_jsons              → List *.json files for a given project.
- GET  /preview_qal                 → Return the parsed JSON of a selected Q&L file.

Pre‑labeling job protocol
-------------------------
POST /prelabel/start
  Request JSON:
    {
      "project_name": str,          # Label Studio project name
      "model": str,                 # Ollama model name (e.g., "gemma:latest")
      "system_prompt": str,         # system prompt to steer extraction
      "qal_file": str               # e.g., "questions_and_labels.json"
    }
  Response (202):
    {"status": "accepted", "job_id": "<uuid-like id>"}

GET /prelabel/status/<job_id>
  Response (200):
    {
      "state": "queued" | "running" | "cancelling" | "cancelled" | "done" | "error",
      "progress": 0.0..1.0 | null,
      "total": int | null,
      "done": int | null,
      "message": str | null
    }
  Response (404): {"error": "unknown job_id"}

POST /prelabel/cancel/<job_id>
  Response (200):
    {"status": "cancel_requested"}  # or {"status": "already_finished"}
  Response (404):
    {"error": "unknown job_id"}

Notes
-----
- The `try_wrap` helper standardizes success/error JSON envelopes for sync routes.
- Q&L routes use a fixed base path: `data/projects/<project>/...` and validate
  against path traversal.
- Ports and allowed origins are defined as constants in this file.

cURL examples
-------------
# Start a job
curl -s -X POST http://localhost:5001/prelabel/start \
  -H "Content-Type: application/json" \
  -d '{"project_name":"MyProject","model":"gemma:latest","system_prompt":"...","qal_file":"questions_and_labels.json"}'

# Poll status
curl -s http://localhost:5001/prelabel/status/<job_id>

# Cancel job
curl -s -X POST http://localhost:5001/prelabel/cancel/<job_id>
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Route implementations
from routes.create_project import create_project_main_from_payload

from routes.load_ollama_models import (
    load_ollama_models_main_wrapper as load_ollama_models_main,
)
from routes.prelabel_complete_project import prelabel_complete_project_main
from routes.upload_tasks import upload_tasks_main_from_payload
from routes.check_project_exists import check_project_exists
from routes.list_html_folders import list_html_subfolders
from routes.questions_and_labels import (
    list_projects_route,
    list_qal_jsons_route,
    preview_qal_route,
)
from routes.prelabel_jobs import start_job, read_status as read_prelabel_status, cancel_job as cancel_prelabel_job


# --- Configuration constants (adjust here if needed) ---
FRONTEND_ORIGIN = "http://localhost:5173"
APP_PORT = 5001
# -------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=[FRONTEND_ORIGIN])

def try_wrap(fn):
    """
    Execute a callable and standardize its JSON response.

    The callable is expected to return a value that represents logs or a result.
    On success, wraps it as {"status": "success", "logs": <value>}.
    On exception, returns {"status": "error", "error": "<message>"} with HTTP 500.
    """
    try:
        logs = fn()
        return jsonify({"status": "success", "logs": logs}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/create_project", methods=["POST"])
def create_project():
    """
    Create a project in Label Studio and persist its question/label config.

    Request JSON:
      {
        "title": str,
        "questions": [str, ...],
        "labels": [str, ...],
        "token": str  // Label Studio legacy token
      }

    Response:
      {"status": "success", "logs": [...]}
    """
    payload = request.get_json()
    return try_wrap(lambda: create_project_main_from_payload(payload))

@app.route("/load_models", methods=["POST"])
def load_models():
    """
    Ensure required Ollama models are present/loaded.

    Request:  JSON as required by `load_ollama_models_main()`.
    Response: {"status": "success", "logs": [...]}
    """
    return try_wrap(load_ollama_models_main)


# app.py (orchestrator) – replace the existing /prelabel_project route
@app.route("/prelabel_project", methods=["POST"])
def prelabel_project():
    """
    Start pre‑labelling for a given project (synchronous, returns logs).

    Request JSON (all required):
      {
        "project_name": str,            # Label Studio project title
        "model": str,                   # e.g. "gemma:latest"
        "system_prompt": str,           # system prompt for the ML backend
        "qal_file": str,                # filename in data/projects/<project_name>/
        "token": str                    # Label Studio legacy token
      }
    """
    payload = request.get_json() or {}
    return try_wrap(lambda: prelabel_complete_project_main(payload))


@app.route("/upload_tasks", methods=["POST"])
def upload_tasks():
    """
    Upload HTML tasks from a given folder to an existing Label Studio project.

    Request JSON:
      {
        "project_name": str,
        "token": str,           // Label Studio legacy token
        "html_folder": str      // subfolder name inside data/htmls
      }

    Response:
      {"status": "success", "logs": [...]}
    """
    payload = request.get_json()
    return try_wrap(lambda: upload_tasks_main_from_payload(payload))


@app.route("/health", methods=["GET"])
def health():
    """
    Liveness probe.

    Response:
      {"status": "ok"}
    """
    return jsonify({"status": "ok"}), 200


@app.route("/project_exists", methods=["POST"])
def project_exists():
    """
    Check whether a Label Studio project with the given title already exists.

    Request JSON:
      {"title": str}

    Response:
      {"exists": bool}
    """
    return check_project_exists()


@app.route("/list_html_subfolders", methods=["GET"])
def list_html_subfolders_route():
    """
    List subfolders available under data/htmls for task upload selection.

    Request:  No body.
    Response: ["folder_a", "folder_b", ...]
    """
    return list_html_subfolders()

@app.route("/list_projects", methods=["GET"])
def list_projects():
    """
    List project directories under data/projects.

    Request:  No body.
    Response: ["ProjectA", "ProjectB", ...]
    """
    return list_projects_route()


@app.route("/list_qal_jsons", methods=["GET"])
def list_qal_jsons():
    """
    List Questions & Labels JSON files inside a given project folder.

    Query parameters:
      - project: str (required)  // name of folder under data/projects

    Response: ["questions_and_labels.json", "custom_qal.json", ...]
    """
    return list_qal_jsons_route()


@app.route("/preview_qal", methods=["GET"])
def preview_qal():
    """
    Preview (return) the parsed JSON content of a Q&L file for a project.

    Query parameters:
      - project: str (required)  // project folder name
      - file:    str (required)  // JSON filename within that project

    Response: <parsed JSON>  // dict or list, as stored in the file
    """
    return preview_qal_route()

@app.route("/prelabel/start", methods=["POST"])
def prelabel_start():
    """
    Start pre‑labeling as an asynchronous job (returns 202 + job_id).

    Request JSON (all required):
      {
        "project_name": str,        # Label Studio project name
        "model": str,               # Ollama model name, e.g. "gemma:latest"
        "system_prompt": str,       # system prompt to steer extraction
        "qal_file": str             # Questions & Labels JSON filename in data/projects/<project_name>/
      }

    Responses:
      202 Accepted:
        {"status": "accepted", "job_id": "<uuid>"}
      400 Bad Request:
        {"status": "error", "error": "missing field: <key>"}

    # curl example:
    # curl -s -X POST http://localhost:5001/prelabel/start \
    #   -H "Content-Type: application/json" \
    #   -d '{"project_name":"MyProject","model":"gemma:latest","system_prompt":"...","qal_file":"questions_and_labels.json"}'
    """
    payload = request.get_json() or {}
    # Validate minimal fields
    for k in ("project_name", "model", "system_prompt", "qal_file"):
        if not payload.get(k):
            return jsonify({"status": "error", "error": f"missing field: {k}"}), 400
    job_id = start_job(payload)
    return jsonify({"status": "accepted", "job_id": job_id}), 202


@app.route("/prelabel/status/<job_id>", methods=["GET"])
def prelabel_status(job_id):
    """
    Get the current status of a pre‑labeling job.

    Path params:
      - job_id: str

    Responses:
      200 OK: status JSON
      404 Not Found: {"status": "error", "error": "unknown job_id"}
    """
    s = read_prelabel_status(job_id)
    if not s:
        return jsonify({"status": "error", "error": "unknown job_id"}), 404
    return jsonify(s), 200


@app.route("/prelabel/cancel/<job_id>", methods=["POST"])
def prelabel_cancel(job_id):
    """
    Request cancellation of a running pre‑labeling job.

    Path params:
      - job_id: str

    Responses:
      200 OK:
        {"status": "cancel_requested"}      # or {"status": "already_finished"}
      404 Not Found:
        {"error": "unknown job_id"}

    # curl example:
    curl -s -X POST http://localhost:5001/prelabel/cancel/<job_id> \
    -H "Content-Type: application/json"
    """
    res = cancel_prelabel_job(job_id)
    if "error" in res:
        return jsonify(res), 404
    return jsonify(res), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)