# tests/smoke/test_labelstudio_version.py

import requests


def test_labelstudio_is_alive(labelstudio_base):
    resp = requests.get(f"{labelstudio_base}/api/version", timeout=5)
    assert resp.status_code == 200
