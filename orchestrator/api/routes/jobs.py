# orchestrator/api/routes/jobs.py

from domain.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_status,
)
from flask import request


def register(app, ok):
    @app.route("/prelabel_project", methods=["POST"])
    def prelabel_project():
        payload = request.get_json() or {}
        return ok(lambda: enqueue_prelabel_job(payload))

    @app.route("/prelabel/status/<job_id>", methods=["GET"])
    def compat_status(job_id):
        return ok(lambda: get_job_status(job_id))

    @app.route("/prelabel/cancel/<job_id>", methods=["POST"])
    def compat_cancel(job_id):
        return ok(lambda: cancel_prelabel_job(job_id))
