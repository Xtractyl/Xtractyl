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
        lambda cmd, run_repo: {"job_id": "123", "state": "RUNNING"},
    )
    res = client.get("/prelabel/status/123")
    assert res.status_code == 200
    data = res.get_json()
    assert data["job_id"] == "123"
    assert data["state"] == "RUNNING"


def test_prelabel_status_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.get_job_status",
        lambda cmd, run_repo: {"wrong_field": "oops"},
    )
    res = client.get("/prelabel/status/123")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


# --- prelabel_project ---


def test_prelabel_project_missing_token_returns_401(client):
    res = client.post(
        "/prelabel_project",
        json={
            "project_name": "test",
            "model": "llama3.1:8b",
            "system_prompt": "test",
        },
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_prelabel_project_missing_fields_returns_422(client):
    res = client.post(
        "/prelabel_project",
        headers={"Authorization": "Bearer dummy"},
        json={"project_name": "test"},
    )
    assert res.status_code == 422


def test_prelabel_project_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.enqueue_prelabel_job",
        lambda cmd, run_repo, project_repo, model_repo, queue: {
            "job_id": "123",
            "status_url": "/prelabel/status/123",
            "cancel_url": "/prelabel/cancel/123",
        },
    )
    res = client.post(
        "/prelabel_project",
        headers={"Authorization": "Bearer dummy"},
        json={"project_name": "test", "model": "llama3.1:8b", "system_prompt": "test"},
    )
    assert res.status_code == 200
    assert res.get_json() == {
        "job_id": "123",
        "status_url": "/prelabel/status/123",
        "cancel_url": "/prelabel/cancel/123",
    }


# --- prelabel/cancel ---


def test_prelabel_cancel_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.cancel_prelabel_job",
        lambda cmd, run_repo: {"job_id": "123", "status": "cancel_requested"},
    )
    res = client.post("/prelabel/cancel/123")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "cancel_requested"


def test_prelabel_cancel_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.jobs.cancel_prelabel_job",
        lambda cmd, run_repo: {"wrong_field": "oops"},
    )
    res = client.post("/prelabel/cancel/123")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"
