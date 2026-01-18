# api/routes/health.py
from flask import jsonify


def register(app, ok=None):
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200
