from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

LOGFILE_PATH = "/logs/docling.log"
PDF_DIR = "/pdfs"
HTML_DIR = "/htmls"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.FileHandler(LOGFILE_PATH), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

PDF_DIR = "/pdfs"
HTML_DIR = "/htmls"

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

    results = []

    for file in files:
        filename = file.filename
        if not filename.lower().endswith(".pdf"):
            results.append({
                "file": filename,
                "status": "error",
                "message": "Not a PDF"
            })
            continue

        pdf_path = os.path.join(pdf_target_dir, filename)
        try:
            file.save(pdf_path)
            logger.info(f"📥 Datei gespeichert: {pdf_path}")

            subprocess.run([
                "docling", pdf_path,
                "--from", "pdf",
                "--to", "html",
                "--output", html_target_dir
            ], check=True)

            html_filename = os.path.splitext(filename)[0] + ".html"
            logger.info(f"✅ Konvertiert: {filename} → {html_filename}")

            results.append({
                "file": filename,
                "status": "ok"
            })

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Docling-Konvertierung fehlgeschlagen: {e}")
            results.append({
                "file": filename,
                "status": "error",
                "message": "Conversion failed"
            })
        except Exception as e:
            logger.exception("❌ Unerwarteter Fehler")
            results.append({
                "file": filename,
                "status": "error",
                "message": str(e)
            })

    return jsonify({"results": results})

@app.route("/list-subfolders", methods=["GET"])
def list_subfolders():
    try:
        logger.info("📁 Liste Unterordner in /pdfs ...")
        entries = os.listdir(PDF_DIR)
        logger.info(f"🔍 Gefundene Einträge: {entries}")

        subfolders = [
            name for name in entries
            if os.path.isdir(os.path.join(PDF_DIR, name))
        ]
        logger.info(f"✅ Rückgabe: {subfolders}")
        return jsonify(subfolders)

    except Exception as e:
        logger.exception("❌ Fehler beim Auflisten der Unterordner")
        return jsonify([]), 500
    
@app.route("/list-files", methods=["GET"])
def list_files_in_folder():
    folder = request.args.get("folder", "").strip()
    if not folder:
        return jsonify([]), 400

    target_dir = os.path.join(PDF_DIR, folder)
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        return jsonify([]), 404

    try:
        files = [
            f for f in os.listdir(target_dir)
            if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(target_dir, f))
        ]
        return jsonify(files)
    except Exception as e:
        logger.exception("Fehler beim Auflisten der Dateien")
        return jsonify([]), 500
    
if __name__ == "__main__":
    logger.info("🚀 Docling Flask-Server wird gestartet ...")
    app.run(host="0.0.0.0", port=5004)