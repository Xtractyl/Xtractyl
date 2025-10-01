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


# --- Configuration constants (adjust here if needed) ---
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}")
APP_PORT = int(os.getenv("ORCH_PORT", "5001"))
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)