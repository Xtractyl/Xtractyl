# orchestrator/tests/unit/test_jobs_route.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- prelabel/status ---


def test_prelabel_status_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.get_job_status",
        lambda cmd: {"job_id": "123", "state": "RUNNING"},
    )
    res = client.get("/prelabel/status/123")
    assert res.status_code == 200
    data = res.get_json()
    assert data["job_id"] == "123"
    assert data["state"] == "RUNNING"


def test_prelabel_status_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.get_job_status",
        lambda cmd: {"wrong_field": "oops"},
    )
    res = client.get("/prelabel/status/123")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"
