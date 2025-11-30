# orchestrator/routes/elist_html_folders.py
import os

from flask import jsonify


def list_html_subfolders():
    base_dir = os.path.join("data", "htmls")
    try:
        subfolders = [
            name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))
        ]
        return jsonify(subfolders), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
