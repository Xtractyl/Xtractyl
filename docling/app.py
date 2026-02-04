import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from flask import Flask, jsonify, request
from flask_cors import CORS
from utils.conversion_worker import run_conversion
from utils.job_files import read_latest_status, write_status

# In-memory job registry: job_id -> {"future": Future, "stop": Event}
JOBS = {}

app = Flask(__name__)
CORS(app, origins=[f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"])

PORT = int(os.getenv("DOCLING_PORT", "5004"))

# --- Paths ---
PDF_DIR = "/pdfs"
HTML_DIR = "/htmls"

# --- Threading ---
executor = ThreadPoolExecutor(max_workers=2)

# =========================
# Job lifecycle endpoints
# =========================


@app.route("/uploadpdfs", methods=["POST"])
def upload_and_convert():
    """
    Accept uploaded PDFs and start a background conversion job.
    Returns a job_id that can be polled for status.
    """
    if "files" not in request.files or "folder" not in request.form:
        return jsonify({"error": "Missing 'files' or 'folder'"}), 400

    folder = request.form["folder"].strip()
    files = request.files.getlist("files")

    if not folder:
        return jsonify({"error": "Folder name is empty"}), 400

    pdf_target_dir = os.path.join(PDF_DIR, folder)
    html_target_dir = os.path.join(HTML_DIR, folder)
    os.makedirs(pdf_target_dir, exist_ok=True)
    os.makedirs(html_target_dir, exist_ok=True)

    saved_pdf_paths = []
    for f in files:
        name = f.filename
        if not name.lower().endswith(".pdf"):
            continue
        path = os.path.join(pdf_target_dir, name)
        f.save(path)
        saved_pdf_paths.append(path)

    if not saved_pdf_paths:
        return jsonify({"error": "No valid PDF files uploaded"}), 400

    job_id = uuid.uuid4().hex
    write_status(job_id, state="queued", progress=0, total=len(saved_pdf_paths), done=0)

    stop_event = Event()
    future = executor.submit(run_conversion, job_id, saved_pdf_paths, html_target_dir, stop_event)
    JOBS[job_id] = {"future": future, "stop": stop_event}

    return jsonify({"job_id": job_id, "message": "accepted"}), 202


@app.route("/job_status/<job_id>", methods=["GET"])
def job_status(job_id):
    """Return latest status for a job_id from the status file."""
    data = read_latest_status(job_id)
    if not data:
        return jsonify({"error": "unknown or not ready"}), 404
    return jsonify(data), 200


@app.route("/cancel_job/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """
    Request cancellation of a running job.
    If the job is already finished, return 200 with the final state.
    """
    info = JOBS.get(job_id)
    status = read_latest_status(job_id)  # may be None

    if not info:
        if status and status.get("state") in ("done", "error", "cancelled"):
            return jsonify({"status": "already_finished", "state": status.get("state")}), 200
        return jsonify({"error": "unknown job_id"}), 404

    info["stop"].set()
    try:
        _ = info["future"].cancel()
    except Exception:
        pass

    write_status(
        job_id, state="cancelling", progress=None, total=None, done=None, message="cancel requested"
    )

    return jsonify({"status": "cancel_requested"}), 200


# =========================
# Helper listing endpoints
# =========================


@app.route("/list-subfolders", methods=["GET"])
def list_subfolders():
    """List subdirectories inside /pdfs to help the UI suggest targets."""
    try:
        entries = os.listdir(PDF_DIR)
        subfolders = [
            n
            for n in entries
            if os.path.isdir(os.path.join(PDF_DIR, n)) and n != "Evaluation_Set_Do_Not_Delete"
        ]
        return jsonify(subfolders)
    except Exception:
        return jsonify([]), 500


@app.route("/list-files", methods=["GET"])
def list_files_in_folder():
    """List PDF files inside /pdfs/<folder>."""
    folder = request.args.get("folder", "").strip()
    if not folder:
        return jsonify([]), 400

    target_dir = os.path.join(PDF_DIR, folder)
    if not os.path.isdir(target_dir):
        return jsonify([]), 404

    try:
        files = [
            f
            for f in os.listdir(target_dir)
            if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(target_dir, f))
        ]
        return jsonify(files)
    except Exception:
        return jsonify([]), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
