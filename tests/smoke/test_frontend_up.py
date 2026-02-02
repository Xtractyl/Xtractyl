# tests/smoke/test_frontend_up.py
import os

import requests


def test_frontend_serves_index():
    base = os.getenv("FRONTEND_BASE", "http://localhost:5173")
    r = requests.get(base + "/", timeout=10)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
