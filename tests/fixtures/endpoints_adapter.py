# tests/fixtures/endpoints_adapter.py
import os
from urllib.parse import urljoin, urlencode

ORCH_BASE = os.getenv("ORCH_BASE", "http://orchestrator:5001").rstrip("/")
DOC_BASE  = os.getenv("DOCLING_BASE", "http://docling:5004").rstrip("/")

# --- Orchestrator endpoints (from your Flask app) ---
_ORCH = {
    "health":               "/health",                 # GET
    "create_project":       "/create_project",         # POST
    "load_models":          "/load_models",            # POST
    "prelabel_project":     "/prelabel_project",       # POST
    "upload_tasks":         "/upload_tasks",           # POST
    "project_exists":       "/project_exists",         # POST
    "list_html_subfolders": "/list_html_subfolders",   # GET
    "list_projects":        "/list_projects",          # GET
    "list_qal_jsons":       "/list_qal_jsons",         # GET ?project=<name>
    "preview_qal":          "/preview_qal",            # GET ?project=<name>&file=<name>
}

# --- Docling endpoints (from your Flask app) ---
_DOC = {
    "uploadpdfs":     "/uploadpdfs",           # POST (multipart: files[]=.., folder=..)
    "job_status":     "/job_status/{job_id}",  # GET
    "job_log":        "/job_log/{job_id}",     # GET (text/plain stream)
    "cancel_job":     "/cancel_job/{job_id}",  # POST
    "list_subfolders":"/list-subfolders",      # GET
    "list_files":     "/list-files",           # GET ?folder=<name>
}

def _join(base: str, path: str) -> str:
    return urljoin(base + "/", path.lstrip("/"))

# ---- Public helpers ---------------------------------------------------------

def orch(key: str, **query) -> str:
    """Build an Orchestrator URL. Optional query params via kwargs."""
    if key not in _ORCH:
        raise KeyError(f"unknown orchestrator endpoint: {key}")
    url = _join(ORCH_BASE, _ORCH[key])
    if query:
        url += "?" + urlencode(query, doseq=True)
    return url

def doc(key: str, *, job_id: str | None = None, **query) -> str:
    """Build a Docling URL. Pass job_id for job_* endpoints; query params via kwargs."""
    if key not in _DOC:
        raise KeyError(f"unknown docling endpoint: {key}")
    path = _DOC[key]
    if "{job_id}" in path:
        if not job_id:
            raise ValueError(f"{key} requires job_id")
        path = path.format(job_id=job_id)
    url = _join(DOC_BASE, path)
    if query:
        url += "?" + urlencode(query, doseq=True)
    return url