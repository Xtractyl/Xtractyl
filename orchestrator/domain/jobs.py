# orchestrator/domain/jobs.py
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import redis

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


REQUIRED_FIELDS = ("project_name", "model", "system_prompt", "token")


def enqueue_prelabel_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    for k in REQUIRED_FIELDS:
        if not payload.get(k):
            raise ValueError(f"Missing field: {k}")

    job_id = payload.get("job_id")
    if not job_id:
        # prefer uuid, but keep it minimal here
        job_id = str(int(time.time() * 1000))
        payload["job_id"] = job_id

    r.hset(
        _status_key(job_id),
        mapping={
            "state": "PENDING",
            "progress": "0",
            "project_name": payload["project_name"],
            "model": payload["model"],
            "created_at": str(time.time()),
            "error": "",
        },
    )
    r.delete(_result_key(job_id))
    r.delete(_logs_key(job_id))

    r.rpush(QUEUE, json.dumps(payload))

    return {
        "job_id": job_id,
        "status_url": f"/jobs/{job_id}",
        "logs_url": f"/jobs/{job_id}/logs",
        "cancel_url": f"/prelabel/cancel/{job_id}",
    }


def get_job_status(job_id: str) -> Dict[str, Any]:
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


def get_job_logs_since(job_id: str, start: int = 0) -> Dict[str, Any]:
    lines = r.lrange(_logs_key(job_id), start, -1) or []
    to = start + len(lines) - 1 if lines else start
    return {"job_id": job_id, "from": start, "to": to, "lines": lines}


def cancel_prelabel_job(job_id: str) -> Dict[str, Any]:
    # mark cancel request; worker checks it between tasks
    r.hset(_status_key(job_id), "state", "CANCEL_REQUESTED")
    return {"job_id": job_id, "status": "cancel_requested"}
