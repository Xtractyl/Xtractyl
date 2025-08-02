import os
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union

# Base directory for per-job artifacts
DOC_LOG_DIR = "/logs/docling"
os.makedirs(DOC_LOG_DIR, exist_ok=True)


def status_path(job_id: str) -> str:
    """Return absolute path to the status JSON file of a job."""
    return os.path.join(DOC_LOG_DIR, f"{job_id}.status.json")


def log_path(job_id: str) -> str:
    """Return absolute path to the JSONL log file of a job."""
    return os.path.join(DOC_LOG_DIR, f"{job_id}.jsonl")


def write_status(job_id: str, **payload: Any) -> None:
    """
    Atomically write the current job status to disk.

    Parameters
    ----------
    job_id : str
        Identifier of the job.
    payload : Any
        Arbitrary serializable key-value pairs describing status.
        Typical keys: state, progress, total, done, message.
    """
    path = status_path(job_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)  # atomic on POSIX


def read_latest_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Read the most recent job status from disk.

    Returns
    -------
    dict | None
        Parsed JSON dict if available and valid; None if file does not exist
        or is temporarily unreadable (e.g., mid-write).
    """
    path = status_path(job_id)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # File may be read mid-write; caller can retry later.
        return None


def append_log(job_id: str, entry: Union[str, Dict[str, Any]]) -> None:
    """
    Append a log entry for a job to a JSONL file.

    Parameters
    ----------
    job_id : str
        Identifier of the job.
    entry : str | dict
        If str, it will be wrapped as {"message": <str>}.
        If dict, it will be written as-is after adding a timestamp ("ts") if missing.

    Notes
    -----
    - Each line is a standalone JSON object (JSONL).
    - Includes an ISO 8601 UTC timestamp under key "ts".
    """
    record: Dict[str, Any]
    if isinstance(entry, str):
        record = {"message": entry}
    else:
        record = dict(entry)  # shallow copy

    record.setdefault("ts", datetime.utcnow().isoformat(timespec="seconds") + "Z")

    with open(log_path(job_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")