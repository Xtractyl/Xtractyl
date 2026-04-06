# orchestrator/tests/unit/test_evaluation_route.py

import pytest
from app import create_app
from domain.errors import AlreadyExists


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


# --- save_as_gt_set ---


def test_save_as_gt_set_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.save_as_gt_set",
        lambda cmd, token: {"gt_set_name": "My_GT_Set"},
    )
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "my_project", "gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["gt_set_name"] == "My_GT_Set"


def test_save_as_gt_set_missing_token_returns_401(client):
    res = client.post(
        "/save-as-gt-set",
        json={"source_project": "my_project", "gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_save_as_gt_set_missing_source_project_returns_422(client):
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 422


def test_save_as_gt_set_missing_gt_set_name_returns_422(client):
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "my_project"},
    )
    assert res.status_code == 422


def test_save_as_gt_set_empty_source_project_returns_422(client):
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "", "gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 422


def test_save_as_gt_set_empty_gt_set_name_returns_422(client):
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "my_project", "gt_set_name": ""},
    )
    assert res.status_code == 422


def test_save_as_gt_set_already_exists_returns_409(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.save_as_gt_set",
        lambda cmd, token: (_ for _ in ()).throw(
            AlreadyExists(code="GT_SET_ALREADY_EXISTS", message="Already exists.")
        ),
    )
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "my_project", "gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 409


def test_save_as_gt_set_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.evaluation.save_as_gt_set",
        lambda cmd, token: {"wrong_field": "oops"},
    )
    res = client.post(
        "/save-as-gt-set",
        headers={"Authorization": "Bearer dummy"},
        json={"source_project": "my_project", "gt_set_name": "My_GT_Set"},
    )
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"
