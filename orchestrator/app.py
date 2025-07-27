from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
from routes.accept_predictions_as_annotations import accept_predictions_main
from routes.compare_predictions_with_annotations import compare_predictions_main
from routes.create_project import create_project_main_from_payload
from routes.export_final_annotations import export_final_annotations_main_wrapper as export_final_annotations_main
from routes.load_ollama_models import load_ollama_models_main_wrapper as load_ollama_models_main
from routes.prelabel_complete_project import prelabel_complete_project_main_wrapper as prelabel_complete_project_main
from routes.upload_tasks import upload_tasks_main_wrapper as upload_tasks_main
from routes.save_questions_labels import save_questions_and_labels_main
from routes.check_project_exists import check_project_exists

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

def run_script(script_name):
    script_path = os.path.join("routes", script_name)
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({
            "status": "success",
            "logs": result.stdout
        }), 200
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "error": e.stderr
        }), 500

def try_wrap(fn):
    try:
        logs = fn()
        # print(logs)  # Optional: zum Debuggen
        return jsonify({
            "status": "success",
            "logs": logs
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/accept_predictions", methods=["POST"])
def accept_predictions():
    return try_wrap(accept_predictions_main)

@app.route("/compare_predictions", methods=["GET"])
def compare_predictions():
    return try_wrap(compare_predictions_main)

@app.route("/create_project", methods=["POST"])
def create_project():
    payload = request.get_json()
    return try_wrap(lambda: create_project_main_from_payload(payload))

@app.route("/export_annotations", methods=["GET"])
def export_annotations():
    return try_wrap(export_final_annotations_main)

@app.route("/load_models", methods=["POST"])
def load_models():
    return try_wrap(load_ollama_models_main)

@app.route("/prelabel_project", methods=["POST"])
def prelabel_project():
    return try_wrap(prelabel_complete_project_main)

@app.route("/upload_tasks", methods=["POST"])
def upload_tasks():
    return try_wrap(upload_tasks_main)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/save_questions_labels", methods=["POST"])
def save_questions_labels():
    payload = request.get_json()
    return try_wrap(lambda: save_questions_and_labels_main(payload))

@app.route("/project_exists", methods=["POST"])
def project_exists():
    return check_project_exists()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)