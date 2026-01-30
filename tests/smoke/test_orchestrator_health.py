# tests/smoke/test_orchestrator_health.py

import requests


def test_orchestrator_health(orch_base):
    resp = requests.get(f"{orch_base}/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
