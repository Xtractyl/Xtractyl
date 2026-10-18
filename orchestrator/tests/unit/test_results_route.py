# orchestrator/tests/unit/test_results_route.py

import pytest
from app import create_app
from domain.errors import InternalError, InvalidState, NotFound


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_results_table_returns_the_table(client, monkeypatch):
    table = {
        "columns": ["task_id", "filename"],
        "rows": [{"task_id": 1, "filename": "a.html"}],
        "total": 1,
    }
    monkeypatch.setattr(
        "api.routes.results.build_results_table",
        lambda cmd, run_repo=None: table,
    )
    res = client.post(
        "/results/table",
        json={"project_name": "test"},
    )
    assert res.status_code == 200
    assert res.get_json() == table


@pytest.mark.parametrize(
    "error, status, code",
    [
        (NotFound(code="RUN_NOT_FOUND", message="m"), 404, "RUN_NOT_FOUND"),
        (InvalidState(code="RUN_NOT_DONE", message="m"), 409, "RUN_NOT_DONE"),
        (InternalError(code="DONE_RUN_WITHOUT_TASKS", message="m"), 500, "DONE_RUN_WITHOUT_TASKS"),
    ],
)
def test_results_table_maps_domain_errors_to_http_errors(client, monkeypatch, error, status, code):
    def raise_error(cmd, run_repo=None):
        raise error

    monkeypatch.setattr("api.routes.results.build_results_table", raise_error)
    res = client.post(
        "/results/table",
        json={"project_name": "test"},
    )
    assert res.status_code == status
    assert res.get_json()["error"] == code


def test_list_projects_ready_for_results_returns_projects(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.results.list_projects_ready_for_results",
        lambda run_repo=None: {"projects": ["a", "b"]},
    )
    res = client.get("/list_projects_ready_for_results")
    assert res.status_code == 200
    assert res.get_json() == {"projects": ["a", "b"]}


def test_list_projects_ready_for_results_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.results.list_projects_ready_for_results",
        lambda run_repo=None: {"wrong_field": "oops"},
    )
    res = client.get("/list_projects_ready_for_results")
    assert res.status_code == 500
    assert res.get_json()["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_results_table_missing_project_name_returns_422(client):
    res = client.post(
        "/results/table",
        json={},
    )
    assert res.status_code == 422


def test_results_table_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.results.build_results_table",
        lambda cmd, run_repo=None: {"wrong_field": "oops"},
    )
    res = client.post(
        "/results/table",
        json={"project_name": "test"},
    )
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"
