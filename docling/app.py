import os
import subprocess
from flask import Flask, jsonify
import logging

# Zentrales Logfile (Containerpfad → wird auf root/logs gemountet)
LOGFILE_PATH = "/logs/docling.log"

# Logger-Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGFILE_PATH),
        logging.StreamHandler()  # Optional: auch in Docker logs sichtbar
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PDF_DIR = "/pdfs"
HTML_DIR = "/htmls"

@app.route("/docling/convert-folder", methods=["POST"])
def convert_all_pdfs():
    logger.info("🔁 Starte Batch-Konvertierung aller PDFs im Ordner /pdfs ...")
    try:
        results = []
        for filename in os.listdir(PDF_DIR):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(PDF_DIR, filename)
                logger.info(f"➡️  Konvertiere {filename} ...")

                subprocess.run([
                    "docling", pdf_path,
                    "--from", "pdf",
                    "--to", "html",
                    "--output", HTML_DIR
                ], check=True)

                html_filename = os.path.splitext(filename)[0] + ".html"
                results.append({
                    "pdf": filename,
                    "html": html_filename
                })

        logger.info(f"✅ {len(results)} PDF(s) erfolgreich konvertiert.")
        return jsonify({
            "converted": results,
            "message": f"{len(results)} PDF(s) converted."
        })

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Docling-Konvertierung fehlgeschlagen: {e}")
        return jsonify({"error": f"Docling failed: {str(e)}"}), 500

    except Exception as e:
        logger.exception("❌ Unerwarteter Fehler während der Konvertierung")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("🚀 Docling Flask-Server wird gestartet ...")
    app.run(host="0.0.0.0", port=5004)