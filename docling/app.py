import os
import subprocess
import tempfile

import requests as req
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils.logging_utils import dev_logger, safe_logger

app = Flask(__name__)
CORS(app, origins=[f"http://localhost:{os.getenv('FRONTEND_PORT', '5173')}"])

PORT = int(os.getenv("DOCLING_PORT", "5004"))


safe_logger.info("docling_starting")


@app.route("/convert", methods=["POST"])
def convert_from_url():
    """
    Accept a pdf_url, download it, convert to HTML via Docling CLI,
    return the HTML content as JSON.
    """

    data = request.get_json(silent=True) or {}
    pdf_url = data.get("pdf_url")
    filename = data.get("filename", "document.pdf")

    if not pdf_url:
        return jsonify({"error": "Missing pdf_url"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, filename)
        html_dir = os.path.join(tmpdir, "html_out")
        os.makedirs(html_dir, exist_ok=True)

        # Download PDF
        try:
            r = req.get(pdf_url, timeout=60)
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            safe_logger.error("pdf_download_failed")
            if dev_logger:
                dev_logger.exception("pdf_download_failed_dev | error=%s", str(e))
            return jsonify({"error": "Failed to download PDF"}), 502

        # Convert via Docling CLI
        cmd = ["docling", pdf_path, "--from", "pdf", "--to", "html", "--output", html_dir]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            safe_logger.error("docling_conversion_failed")
            if dev_logger:
                dev_logger.exception("docling_conversion_failed_dev | exit=%s", str(e.returncode))
            return jsonify({"error": "Docling conversion failed"}), 500

        # Read HTML output
        html_filename = os.path.splitext(filename)[0] + ".html"
        html_path = os.path.join(html_dir, html_filename)
        if not os.path.exists(html_path):
            # Try to find any html file
            html_files = [f for f in os.listdir(html_dir) if f.endswith(".html")]
            if not html_files:
                return jsonify({"error": "No HTML output found"}), 500
            html_path = os.path.join(html_dir, html_files[0])

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

    return jsonify({"html": html_content}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
