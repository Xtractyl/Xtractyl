# tests/smoke/test_labelstudio_version.py

import time

import requests


def test_labelstudio_is_alive(labelstudio_base):
    url = f"{labelstudio_base}/api/version"

    deadline = time.time() + 90
    last_err = None

    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()

                # Smoke-level assertion: bekannte stabile Keys
                assert isinstance(data, dict)
                assert "edition" in data
                return
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as e:
            last_err = repr(e)

        time.sleep(2)

    raise AssertionError(f"Label Studio not ready after 90s. Last error: {last_err}")
