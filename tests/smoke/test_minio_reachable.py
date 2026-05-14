import requests


def test_minio_reachable(minio_base):
    response = requests.get(f"{minio_base}/minio/health/live", timeout=5)
    assert response.status_code == 200
