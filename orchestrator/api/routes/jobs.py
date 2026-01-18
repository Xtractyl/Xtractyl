# orchestrator/api/routes/jobs.py

from flask import request

from orchestrator.api.domain.jobs import (
    cancel_prelabel_job,
    enqueue_prelabel_job,
    get_job_logs_since,
    get_job_status,
)


def register(app, ok):
    @app.route("/jobs/<job_id>", methods=["GET"])
    def route_job_status(job_id):
        return ok(lambda: get_job_status(job_id))

    @app.route("/jobs/<job_id>/logs", methods=["GET"])
    def route_job_logs(job_id):
        try:
            start = int(request.args.get("from", "0"))
        except ValueError:
            start = 0
        return ok(lambda: get_job_logs_since(job_id, start))

    @app.route("/prelabel_project", methods=["POST"])
    def prelabel_project():
        payload = request.get_json() or {}
        return ok(lambda: enqueue_prelabel_job(payload))

    @app.route("/prelabel/status/<job_id>", methods=["GET"])
    def compat_status(job_id):
        return ok(lambda: get_job_status(job_id))

    @app.route("/prelabel/logs/<job_id>", methods=["GET"])
    def compat_logs(job_id):
        try:
            start = int(request.args.get("from", "0"))
        except ValueError:
            start = 0
        return ok(lambda: get_job_logs_since(job_id, start))

    @app.route("/prelabel/cancel/<job_id>", methods=["POST"])
    def compat_cancel(job_id):
        return ok(lambda: cancel_prelabel_job(job_id))
