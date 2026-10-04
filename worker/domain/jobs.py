# worker/domain/jobs.py
from __future__ import annotations

from contracts.jobs import JobPayload
from infrastructure.orchestrator import send_job_failed
from utils.logging_utils import dev_logger, safe_logger

from domain.prelabel_project import prelabel_project


def run_job(job: JobPayload) -> None:
    safe_logger.info("job_picked_up | job_id=%s", job.job_id)
    try:
        prelabel_project(job)
    except Exception as e:
        send_job_failed(job.job_id, str(e))
        safe_logger.error("job_failed | job_id=%s", job.job_id)
        if dev_logger:
            dev_logger.exception("job_failed_dev | job_id=%s", job.job_id)
