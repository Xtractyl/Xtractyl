# orchestrator/api/routes/results.py

from flask import request

from api.domain.results import build_results_table


def register(app, ok):
    @app.route("/get_results_table", methods=["POST"])
    def get_results_table_route():
        payload = request.get_json() or {}
        project_name = payload.get("project_name")
        token = payload.get("token")

        def run():
            if not project_name or not token:
                raise ValueError("project_name and token are required")
            return build_results_table(token, project_name)

        return ok(run)
