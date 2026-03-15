# orchestrator/tests/unit/test_evaluation_route.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- /evaluate-ai/projects ---


def test_evaluate_ai_projects_missing_token_returns_401(client):
    res = client.get("/evaluate-ai/projects")
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_evaluate_ai_projects_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.list_project_names",
        lambda token: {"names": ["ProjectA", "ProjectB"]},
    )
    res = client.get(
        "/evaluate-ai/projects",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200


# --- /evaluate-ai ---


def test_evaluate_ai_missing_token_returns_401(client):
    res = client.post(
        "/evaluate-ai",
        json={"groundtruth_project": "gt", "comparison_project": "cmp"},
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_evaluate_ai_missing_groundtruth_returns_422(client):
    res = client.post(
        "/evaluate-ai",
        headers={"Authorization": "Bearer dummy"},
        json={"comparison_project": "cmp"},
    )
    assert res.status_code == 422


def test_evaluate_ai_missing_comparison_returns_422(client):
    res = client.post(
        "/evaluate-ai",
        headers={"Authorization": "Bearer dummy"},
        json={"groundtruth_project": "gt"},
    )
    assert res.status_code == 422


def test_evaluate_ai_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.evaluate_projects",
        lambda cmd: {
            "groundtruth_project": "gt",
            "groundtruth_project_id": 1,
            "comparison_project": "cmp",
            "comparison_project_id": 2,
            "run_at_raw": None,
            "metrics": {},
            "answer_comparison": [],
            "evaluation_output_path": "/dummy/path.json",
        },
    )
    res = client.post(
        "/evaluate-ai",
        headers={"Authorization": "Bearer dummy"},
        json={"groundtruth_project": "gt", "comparison_project": "cmp"},
    )
    assert res.status_code == 200


def test_evaluate_ai_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.evaluate_projects",
        lambda cmd: {"wrong_field": "oops"},
    )
    res = client.post(
        "/evaluate-ai",
        headers={"Authorization": "Bearer dummy"},
        json={"groundtruth_project": "gt", "comparison_project": "cmp"},
    )
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"
