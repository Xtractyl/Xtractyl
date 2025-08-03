# routes/prelabel_jobs.py
import os, json, uuid, logging
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from time import sleep


LOG_DIR = "/logs/prelabel"
os.makedirs(LOG_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> {"future": Future, "stop": Event}

def _status_path(job_id): return os.path.join(LOG_DIR, f"{job_id}.status.json")
def _log(job_id, msg):
    with open(os.path.join(LOG_DIR, f"{job_id}.log"), "a", encoding="utf-8") as f:
        f.write(msg.rstrip()+"\n")

def _write_status(job_id, **payload):
    tmp = _status_path(job_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(payload, f)
    os.replace(tmp, _status_path(job_id))

def read_status(job_id):
    p = _status_path(job_id)
    if not os.path.isfile(p): return None
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except Exception:
        return None

def _worker(job_id, payload, stop: Event):
    """
    payload: {
      "project_name": str,
      "model": str,
      "system_prompt": str,
      "qal_file": str
    }
    Replace the simulated loop with your real prelabel orchestration.
    """
    try:
        steps = 5
        for i in range(steps):
            if stop.is_set():
                _log(job_id, "cancel requested")
                _write_status(job_id, state="cancelled", progress=i/steps, message="cancelled")
                return
            # Simulate work (replace with your actual pipeline call)
            _log(job_id, f"step {i+1}/{steps}")
            _write_status(job_id, state="running", progress=(i+1)/steps, message=f"step {i+1}/{steps}")
            sleep(1.2)

        _write_status(job_id, state="done", progress=1.0, message="finished")
        _log(job_id, "done")
    except Exception as e:
        logging.exception("prelabel worker failed")
        _write_status(job_id, state="error", progress=None, message=str(e))
        _log(job_id, f"error: {e}")

def start_job(payload):
    job_id = uuid.uuid4().hex
    stop = Event()
    _write_status(job_id, state="queued", progress=0.0, message="queued")
    _log(job_id, f"queued: {payload}")
    fut = executor.submit(_worker, job_id, payload, stop)
    JOBS[job_id] = {"future": fut, "stop": stop}
    return job_id

def cancel_job(job_id):
    info = JOBS.get(job_id)
    current = read_status(job_id)
    if not info:
        # Consider it finished/not found; surface current state if present
        if current and current.get("state") in ("done", "error", "cancelled"):
            return {"status": "already_finished", "state": current["state"]}
        return {"error": "unknown job_id"}
    info["stop"].set()
    try: info["future"].cancel()
    except: pass
    _write_status(job_id, state="cancelling", progress=None, message="cancel requested")
    _log(job_id, "cancel requested via API")
    return {"status": "cancel_requested"}