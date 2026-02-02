# tests/smoke/test_ml_backend_health.py

import requests


def test_ml_backend_health(ml_backend_base):
    resp = requests.get(f"{ml_backend_base}/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
