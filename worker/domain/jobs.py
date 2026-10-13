# worker/domain/jobs.py
from __future__ import annotations

from contracts.jobs import JobPayload
from infrastructure.orchestrator import send_job_failed
from utils.logging_utils import dev_logger, safe_logger

from domain.errors import DomainError
from domain.prelabel_project import prelabel_project


def run_job(job: JobPayload) -> None:
    safe_logger.info("job_picked_up | job_id=%s", job.job_id)
    try:
        prelabel_project(job)
    except DomainError as e:
        safe_logger.error("job_failed | job_id=%s", job.job_id, extra={"code": e.code})
        if dev_logger:
            dev_logger.exception(
                "job_failed_dev | job_id=%s", job.job_id, extra={"code": e.code, "meta": e.meta}
            )
        # With the orchestrator down there is nobody to report to (already logged by now).
        if e.code != "ORCHESTRATOR_UNAVAILABLE":
            send_job_failed(job.job_id, str(e))
    except Exception:
        safe_logger.error("job_failed | job_id=%s", job.job_id, extra={"code": "INTERNAL_ERROR"})
        if dev_logger:
            dev_logger.exception("job_failed_dev | job_id=%s", job.job_id)
        send_job_failed(job.job_id, "[INTERNAL_ERROR] Unexpected error in the worker.")
