# tests/smoke/test_labelstudio_version.py

import time

import requests
from requests.exceptions import RequestException


def test_labelstudio_is_alive(labelstudio_base):
    url = f"{labelstudio_base}/api/version"

    deadline = time.time() + 90  # CI ist manchmal langsamer
    last_err = None

    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                # optional: minimal sanity check
                data = resp.json()
                assert "label-studio" in data or "version" in data or "build" in data
                return
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except RequestException as e:
            last_err = repr(e)

        time.sleep(2)

    raise AssertionError(f"Label Studio not ready after 90s. Last error: {last_err}")
