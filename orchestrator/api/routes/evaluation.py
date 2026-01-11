# orchestrator/api/routes/evaluation.py

from flask import jsonify, request
from routes.evaluate_project import evaluate_projects, list_project_names
from routes.groundtruth_qal import get_groundtruth_qal


def register(app, ok):
    @app.route("/evaluate-ai/projects", methods=["GET"])
    def evaluate_ai_projects():
        token = request.args.get("token")
        if not token:
            return jsonify({"status": "error", "error": "token query parameter is required"}), 400

        def run():
            return list_project_names(token)

        return ok(run)

    @app.route("/groundtruth_qal", methods=["GET"])
    def groundtruth_qal():
        return ok(get_groundtruth_qal)

    @app.route("/evaluate-ai", methods=["POST"])
    def evaluate_ai():
        payload = request.get_json() or {}

        token = payload.get("token")
        gt_name = payload.get("groundtruth_project")
        cmp_name = payload.get("comparison_project")

        if not token or not gt_name or not cmp_name:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "token, groundtruth_project, comparison_project are required",
                    }
                ),
                400,
            )

        def run():
            return evaluate_projects(token, gt_name, cmp_name)

        return ok(run)
