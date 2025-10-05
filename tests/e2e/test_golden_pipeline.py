# tests/e2e/test_golden_pipeline.py
import os
import time
import uuid
import pathlib
import requests
import pytest

from fixtures.endpoints_adapter import orch, doc

INPUT_DIR = pathlib.Path(os.getenv("TEST_INPUT_DIR", "/opt/input_pdfs"))
ORCH_TIMEOUT = int(os.getenv("ORCH_TIMEOUT_SECONDS", "120"))
DOCLING_TIMEOUT = int(os.getenv("DOCLING_TIMEOUT_SECONDS", "1800"))

LS_TOKEN = os.getenv("LABEL_STUDIO_LEGACY_TOKEN") or os.getenv("LS_LEGACY_TOKEN")

PROJECT_NAME = os.getenv("E2E_PROJECT_NAME", "e2e_golden_pipeline")

def test_golden_pipeline_end_to_end():
  
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    assert pdfs, f"No PDFs found in {INPUT_DIR}"
    
    folder = f"{PROJECT_NAME}"  
    files = [("files", (p.name, p.open("rb"), "application/pdf")) for p in pdfs]
    data = {"folder": folder}

    r = requests.post(doc("uploadpdfs"), files=files, data=data, timeout=60)
    assert r.status_code in (200, 202), f"uploadpdfs failed: {r.status_code} {r.text}"
    job_id = r.json()["job_id"]

    # wait for docling job to finish
    state = _wait_for_docling_done(job_id, timeout=DOCLING_TIMEOUT)
    assert state == "done", f"Docling job not done, state={state}"



def _wait_for_docling_done(job_id: str, timeout: int = 180, poll_every: float = 1.5) -> str:
    """Polls /job_status/<job_id> unti state in {'done','error','cancelled'} or Timeout."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = requests.get(doc("job_status", job_id=job_id), timeout=10)
        if r.status_code == 200:
            st = r.json()
            last = st.get("state")
            if last in ("done", "error", "cancelled"):
                return last
        time.sleep(poll_every)
    return last or "unknown"