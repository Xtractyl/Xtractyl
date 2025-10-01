import os
import time
import requests

BASE_URL = os.getenv("BASE_URL", "http://orchestrator:5001")

def test_orchestrator_health():
    # simple smoke test checks /health for orchestrator
    deadline = time.time() + 60  # max 60s warten
    last_err = None
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            assert r.status_code in (200, 204), f"unexpected status: {r.status_code}"
            return  # success
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise AssertionError(f"Orchestrator /health not available: {last_err}")