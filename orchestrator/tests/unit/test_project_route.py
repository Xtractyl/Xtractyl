# orchestrator/tests/unit/test_create_project_route.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- Happy path ---


def test_list_qal_jsons_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.list_qal_jsons",
        lambda cmd: {"files": ["questions_and_labels.json"]},
    )
    res = client.get("/list_qal_jsons?project=my_project")
    assert res.status_code == 200
    data = res.get_json()
    assert data["files"] == ["questions_and_labels.json"]


def test_create_project_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.create_project_main_from_payload",
        lambda cmd: {"project_id": 42},
    )
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"title": "my_project", "questions": ["Q1"], "labels": ["L1"]},
    )
    assert res.status_code == 200


def test_list_html_subfolders_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.list_html_subfolders",
        lambda: {"subfolders": ["folder1", "folder2"]},
    )
    res = client.get("/list_html_subfolders")
    assert res.status_code == 200
    data = res.get_json()
    assert data["subfolders"] == ["folder1", "folder2"]


# --- Unhappy path ---


def test_create_project_missing_token_returns_401(client):
    res = client.post(
        "/create_project",
        json={"title": "my_project", "questions": ["Q1"], "labels": ["L1"]},
    )
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "TOKEN_REQUIRED"


def test_create_project_missing_title_returns_422(client):
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"questions": ["Q1"], "labels": ["L1"]},
    )
    assert res.status_code == 422


def test_create_project_title_too_short_returns_422(client):
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"title": "ab", "questions": ["Q1"], "labels": ["L1"]},
    )
    assert res.status_code == 422


def test_create_project_empty_questions_returns_422(client):
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"title": "my_project", "questions": [], "labels": ["L1"]},
    )
    assert res.status_code == 422


def test_create_project_empty_labels_returns_422(client):
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"title": "my_project", "questions": ["Q1"], "labels": []},
    )
    assert res.status_code == 422


def test_list_qal_jsons_missing_project_returns_422(client):
    res = client.get("/list_qal_jsons")
    assert res.status_code == 422


def test_list_qal_jsons_empty_project_returns_422(client):
    res = client.get("/list_qal_jsons?project=")
    assert res.status_code == 422
    

def test_create_project_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.create_project_main_from_payload",
        lambda cmd: {"wrong_field": "oops"},
    )
    res = client.post(
        "/create_project",
        headers={"Authorization": "Bearer dummy"},
        json={"title": "my_project", "questions": ["Q1"], "labels": ["L1"]},
    )
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_list_html_subfolders_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.list_html_subfolders",
        lambda: {"wrong_field": "oops"},
    )
    res = client.get("/list_html_subfolders")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_list_qal_jsons_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.projects.list_qal_jsons",
        lambda cmd: {"wrong_field": "oops"},
    )
    res = client.get("/list_qal_jsons?project=my_project")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"



