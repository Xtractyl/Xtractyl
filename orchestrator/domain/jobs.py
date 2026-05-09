# orchestrator/domain/jobs.py
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import redis

from domain.models.jobs import CancelJobCommand, EnqueueJobCommand, JobStatusCommand

REDIS_HOST = os.getenv("REDIS_HOST", "job_queue")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

QUEUE = "prelabel_jobs"
STATUS = "status:"
RESULT = "result:"
LOGS = "logs:"


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


def enqueue_prelabel_job(cmd: EnqueueJobCommand) -> Dict[str, Any]:
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
        "qal_file": cmd.qal_file,
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
