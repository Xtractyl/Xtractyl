# orchestrator/tests/unit/test_evaluation_drift_route.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_evaluation_drift_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "domain.evaluation_drift.get_evaluation_drift",
        lambda cmd: {"series": "Evaluation_Set_Do_Not_Delete", "entries": []},
    )
    res = client.get("/evaluation-drift")
    assert res.status_code == 200
    data = res.get_json()
    assert "series" in data
    assert "entries" in data


def test_evaluation_drift_invalid_query_param_returns_400(client):
    res = client.get("/evaluation-drift?set_name=")
    assert res.status_code == 422
