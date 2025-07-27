# routes/check_project_exists.py
import os
from flask import request, jsonify

def check_project_exists():
    try:
        data = request.get_json()
        title = data.get("title")
        if not title:
            return jsonify({"error": "Missing 'title' in request body"}), 400

        project_path = os.path.join("data", "projects", title)
        exists = os.path.exists(project_path)

        return jsonify({"exists": exists}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500