"""
Xtractyl Orchestrator API
=========================

Flask application exposing orchestration endpoints used by the React frontend.
It wires HTTP routes to the underlying functions in `routes/*`.

Conventions
-----------
- All responses are JSON.
- Success wrapper: {"status": "success", "logs": <list|string|object>}
- Error wrapper:   {"status": "error",   "error": "<message>"}
- CORS is limited to the frontend origin.

Endpoints (overview)
--------------------
POST /accept_predictions         -> Accept model predictions as final annotations.
GET  /compare_predictions        -> Compare predictions with human annotations.
POST /create_project             -> Create a Label Studio project + config.
GET  /export_annotations         -> Export merged/final annotations.
POST /load_models                -> Ensure Ollama models are available.
POST /prelabel_project           -> Kick off pre‑labelling for a project.
POST /upload_tasks               -> Upload HTML tasks to a project.
GET  /health                     -> Liveness probe.
POST /project_exists             -> Check if a project exists by title.
GET  /list_html_subfolders       -> List available HTML subfolders on disk.

Notes
-----
- The `try_wrap` helper standardizes success/error JSON envelopes.
- The `run_script` helper is available if a route needs to invoke a stand‑alone
  Python script (currently not used by the routes below).
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Route implementations
from routes.accept_predictions_as_annotations import accept_predictions_main
from routes.compare_predictions_with_annotations import compare_predictions_main
from routes.create_project import create_project_main_from_payload
from routes.export_final_annotations import (
    export_final_annotations_main_wrapper as export_final_annotations_main,
)
from routes.load_ollama_models import (
    load_ollama_models_main_wrapper as load_ollama_models_main,
)
from routes.prelabel_complete_project import (
    prelabel_complete_project_main_wrapper as prelabel_complete_project_main,
)
from routes.upload_tasks import upload_tasks_main_from_payload
from routes.check_project_exists import check_project_exists
from routes.list_html_folders import list_html_subfolders

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


@app.route("/accept_predictions", methods=["POST"])
def accept_predictions():
    """
    Accept model predictions as final annotations.

    Request:  JSON body as required by `accept_predictions_main()`.
    Response: {"status": "success", "logs": [...]}
    """
    return try_wrap(accept_predictions_main)


@app.route("/compare_predictions", methods=["GET"])
def compare_predictions():
    """
    Compare predictions with existing human annotations.

    Request:  No body.
    Response: {"status": "success", "logs": [...]}
    """
    return try_wrap(compare_predictions_main)


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


@app.route("/export_annotations", methods=["GET"])
def export_annotations():
    """
    Export final/merged annotations from Label Studio.

    Request:  No body.
    Response: {"status": "success", "logs": [... or a path/export info ...]}
    """
    return try_wrap(export_final_annotations_main)


@app.route("/load_models", methods=["POST"])
def load_models():
    """
    Ensure required Ollama models are present/loaded.

    Request:  JSON as required by `load_ollama_models_main()`.
    Response: {"status": "success", "logs": [...]}
    """
    return try_wrap(load_ollama_models_main)


@app.route("/prelabel_project", methods=["POST"])
def prelabel_project():
    """
    Start (orchestrate) pre-labelling for a given project.

    Request:  JSON as required by `prelabel_complete_project_main()`.
    Response: {"status": "success", "logs": [...]}
    """
    return try_wrap(prelabel_complete_project_main)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)