# orchestrator/tests/unit/test_results_route.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_results_table_missing_token_returns_401(client):
    res = client.post(
        "/results/table",
        json={"project_name": "test"},
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_results_table_missing_project_name_returns_400(client):
    res = client.post(
        "/results/table",
        headers={"Authorization": "Bearer dummy"},
        json={},
    )
    assert res.status_code == 422
