# orchestrator/domain/jobs.py
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import redis
from infrastructure.interfaces.repository import (
    PrelabellingRunRepositoryInterface,
    ProjectRepositoryInterface,
)

from domain.errors import NotFound
from domain.models.jobs import (
    CancelJobCommand,
    EnqueueJobCommand,
    JobStatusCommand,
    PrelabelCallbackCommand,
)

REDIS_HOST = os.getenv("REDIS_HOST", "job_queue")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

QUEUE = "prelabel_jobs"
STATUS = "status:"
RESULT = "result:"
LOGS = "logs:"

USE_DB_BACKEND = os.getenv("USE_DB_BACKEND", "0") == "1"


def _status_key(job_id: str) -> str:
    return f"{STATUS}{job_id}"


def _result_key(job_id: str) -> str:
    return f"{RESULT}{job_id}"


def _logs_key(job_id: str) -> str:
    return f"{LOGS}{job_id}"


def get_job_status(cmd: JobStatusCommand):
    job_id = cmd.job_id
    h = r.hgetall(_status_key(job_id)) or {}
    if not h:
        return {"job_id": job_id, "state": "NOT_FOUND"}
    res = r.get(_result_key(job_id))
    out: Dict[str, Any] = {"job_id": job_id, **h}
    if res:
        try:
            out["result"] = json.loads(res)
        except Exception:
            out["result"] = res
    return out


def enqueue_prelabel_job(
    cmd: EnqueueJobCommand,
    run_repo: PrelabellingRunRepositoryInterface,
    project_repo: ProjectRepositoryInterface,
) -> Dict[str, Any]:
    if USE_DB_BACKEND:
        label_studio_id = project_repo.get_label_studio_id(cmd.project_name)
        if not label_studio_id:
            raise NotFound(
                code="PROJECT_NOT_FOUND",
                message="Project not found or has no Label Studio ID.",
            )
        qal = project_repo.get_questions_and_labels(cmd.project_name)
        if not qal:
            raise NotFound(
                code="QAL_NOT_FOUND",
                message="No QAL found for this project.",
            )
        job_id = str(
            run_repo.create_run(
                project=cmd.project_name,
                label_studio_id=label_studio_id,
                model=cmd.model,
                system_prompt=cmd.system_prompt,
                questions_and_labels=qal,
            )
        )

    else:
        job_id = str(int(time.time() * 1000))

    r.hset(
        _status_key(job_id),
        mapping={
            "state": "PENDING",
            "progress": "0",
            "project_name": cmd.project_name,
            "model": cmd.model,
            "created_at": str(time.time()),
            "error": "",
        },
    )
    r.delete(_result_key(job_id))
    r.delete(_logs_key(job_id))

    payload = {
        "job_id": job_id,
        "project_name": cmd.project_name,
        "model": cmd.model,
        "system_prompt": cmd.system_prompt,
        "questions_and_labels": cmd.questions_and_labels,
        "token": cmd.token,
    }
    r.rpush(QUEUE, json.dumps(payload))

    return {
        "job_id": job_id,
        "status_url": f"/prelabel/status/{job_id}",
        "cancel_url": f"/prelabel/cancel/{job_id}",
    }


def cancel_prelabel_job(cmd: CancelJobCommand) -> Dict[str, Any]:
    job_id = cmd.job_id
    r.hset(_status_key(job_id), "state", "CANCEL_REQUESTED")
    return {"job_id": job_id, "status": "cancel_requested"}


def handle_prelabel_callback(
    cmd: PrelabelCallbackCommand, run_repo: PrelabellingRunRepositoryInterface
) -> dict:
    run_repo.set_run_status(int(cmd.job_id), cmd.status, cmd.error)
    return {"status": "ok"}
