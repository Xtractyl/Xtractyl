# orchestrator/api/routes/projects.py

from flask import request
from routes.check_project_exists import check_project_exists
from routes.create_project import create_project_main_from_payload
from routes.list_html_folders import list_html_subfolders
from routes.questions_and_labels import (
    list_projects_route,
    list_qal_jsons_route,
    preview_qal_route,
)
from routes.upload_tasks import upload_tasks_main_from_payload


def register(app, ok):
    @app.route("/create_project", methods=["POST"])
    def create_project():
        payload = request.get_json()
        return ok(lambda: create_project_main_from_payload(payload))

    @app.route("/upload_tasks", methods=["POST"])
    def upload_tasks():
        payload = request.get_json()
        return ok(lambda: upload_tasks_main_from_payload(payload))

    @app.route("/project_exists", methods=["POST"])
    def project_exists():
        return check_project_exists()

    @app.route("/list_html_subfolders", methods=["GET"])
    def list_html_subfolders_route():
        return list_html_subfolders()

    @app.route("/list_projects", methods=["GET"])
    def list_projects():
        return list_projects_route()

    @app.route("/list_qal_jsons", methods=["GET"])
    def list_qal_jsons():
        return list_qal_jsons_route()

    @app.route("/preview_qal", methods=["GET"])
    def preview_qal():
        return preview_qal_route()
