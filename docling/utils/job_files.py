import os, json

DOC_LOG_DIR = "/logs/docling"
os.makedirs(DOC_LOG_DIR, exist_ok=True)

def status_path(job_id: str) -> str:
    return os.path.join(DOC_LOG_DIR, f"{job_id}.status.json")

def log_path(job_id: str) -> str:
    return os.path.join(DOC_LOG_DIR, f"{job_id}.jsonl")

def write_status(job_id: str, **payload):
    path = status_path(job_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)  # atomic

def read_latest_status(job_id: str):
    path = status_path(job_id)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # file was read mid-write: treat as not ready
        return None

def append_log(job_id: str, line: str):
    with open(log_path(job_id), "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")