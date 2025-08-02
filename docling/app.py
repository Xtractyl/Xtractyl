from flask import Flask, request, jsonify, send_from_directory
import os
import logging
from flask_cors import CORS
import uuid
from threading import Event
import json
from concurrent.futures import ThreadPoolExecutor
from utils.conversion_worker import run_conversion
from utils.job_files import write_status, append_log, read_latest_status

JOBS = {}

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# --- Pfade/Logging ---
PDF_DIR = "/pdfs"
HTML_DIR = "/htmls"
DOC_LOG_DIR = "/logs/docling"
LOGFILE_PATH = "/logs/docling.log"
os.makedirs(DOC_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.FileHandler(LOGFILE_PATH), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Threading ---
executor = ThreadPoolExecutor(max_workers=2)

@app.route("/uploadpdfs", methods=["POST"])
def upload_and_convert():
    if 'files' not in request.files or 'folder' not in request.form:
        return jsonify({"error": "Missing files or folder"}), 400

    folder = request.form['folder'].strip()
    files = request.files.getlist('files')
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
    append_log(job_id, f"Queued: {len(saved_pdf_paths)} files in '{folder}'")
    stop_event = Event()                               #
    future = executor.submit(run_conversion, job_id, folder, saved_pdf_paths, html_target_dir, stop_event)
    JOBS[job_id] = {"future": future, "stop": stop_event}  # NEU
    return jsonify({"job_id": job_id, "message": "accepted"}), 202


@app.route("/job_status/<job_id>", methods=["GET"])
def job_status(job_id):
    data = read_latest_status(job_id)
    if not data:
        return jsonify({"error": "unknown or not ready"}), 404
    return jsonify(data), 200

@app.route("/job_log/<job_id>", methods=["GET"])
def job_log(job_id):
    log_file = os.path.join(DOC_LOG_DIR, f"{job_id}.jsonl")
    if not os.path.isfile(log_file):
        return jsonify({"error": "unknown job_id"}), 404
    # komplette JSONL-Datei zurückgeben (plain text)
    def generate():
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                yield line
    return app.response_class(generate(), mimetype="text/plain")

@app.route("/cancel_job/<job_id>", methods=["POST"])
def cancel_job(job_id):
    info = JOBS.get(job_id)
    if not info:
        return jsonify({"error": "unknown job_id"}), 404

    # Signal an den Worker senden
    info["stop"].set()

    # Falls Future noch nicht gestartet ist, versucht cancel() sie zu verhindern
    try:
        _ = info["future"].cancel()
    except Exception:
        pass

    append_log(job_id, "cancel requested via API")
    # Sofort sichtbarer Status (Worker setzt danach 'cancelled', sobald er das Signal sieht)
    write_status(
        job_id,
        state="cancelling",
        progress=None,
        total=None,
        done=None,
        message="cancel requested"
    )

    return jsonify({"status": "cancel_requested"}), 200

@app.route("/list-subfolders", methods=["GET"])
def list_subfolders():
    try:
        entries = os.listdir(PDF_DIR)
        subfolders = [n for n in entries if os.path.isdir(os.path.join(PDF_DIR, n))]
        return jsonify(subfolders)
    except Exception:
        logger.exception("❌ Fehler beim Auflisten der Unterordner")
        return jsonify([]), 500

@app.route("/list-files", methods=["GET"])
def list_files_in_folder():
    folder = request.args.get("folder", "").strip()
    if not folder:
        return jsonify([]), 400
    target_dir = os.path.join(PDF_DIR, folder)
    if not os.path.isdir(target_dir):
        return jsonify([]), 404
    try:
        files = [f for f in os.listdir(target_dir)
                 if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(target_dir, f))]
        return jsonify(files)
    except Exception:
        logger.exception("Fehler beim Auflisten der Dateien")
        return jsonify([]), 500


if __name__ == "__main__":
    logger.info("🚀 Docling Flask-Server wird gestartet ...")
    app.run(host="0.0.0.0", port=5004)