import requests


def test_pgadmin_reachable(pgadmin_base):
    response = requests.get(pgadmin_base, timeout=5)
    assert response.status_code == 200
