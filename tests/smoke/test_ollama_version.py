import requests


def test_ollama_version(ollama_base):
    resp = requests.get(f"{ollama_base}/api/version", timeout=5)
    assert resp.status_code == 200
    assert "version" in resp.json()
