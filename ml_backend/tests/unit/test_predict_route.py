# ml_backend/tests/unit/test_predict_route.py

import pytest
from app import create_app

VALID_PAYLOAD = {
    "job_id": "job-123",
    "task_id": "42",
    "html": "<p>Some content</p>",
    "questions_and_labels": {
        "questions": ["What is the diagnosis?"],
        "labels": ["diagnosis"],
    },
    "llm_config": {
        "ollama_model": "llama3",
        "ollama_base": "http://ollama:11434",
        "system_prompt": "Extract the answer.",
        "llm_timeout_seconds": 20,
    },
    "label_studio_config": {
        "label_studio_url": "http://labelstudio:8080",
        "ls_token": "dummy-token",
    },
}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- happy path ---


def test_predict_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.predict.run_predict",
        lambda cmd: {
            "model_version": "llama3",
            "score": 1.0,
            "result": [],
            "meta": {},
        },
    )
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.get_json()
    assert data["model_version"] == "llama3"


# --- 422 contract violations ---


def test_predict_missing_job_id_returns_422(client):
    payload = {**VALID_PAYLOAD}
    del payload["job_id"]
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_missing_html_returns_422(client):
    payload = {**VALID_PAYLOAD}
    del payload["html"]
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_empty_html_returns_422(client):
    payload = {**VALID_PAYLOAD, "html": ""}
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_missing_questions_returns_422(client):
    payload = {**VALID_PAYLOAD, "questions_and_labels": {"questions": [], "labels": ["L1"]}}
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_missing_llm_config_returns_422(client):
    payload = {**VALID_PAYLOAD}
    del payload["llm_config"]
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_missing_label_studio_config_returns_422(client):
    payload = {**VALID_PAYLOAD}
    del payload["label_studio_config"]
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_predict_empty_body_returns_422(client):
    res = client.post("/predict", json={})
    assert res.status_code == 422


# --- 502 external service error ---


def test_predict_label_studio_unreachable_returns_502(client, monkeypatch):
    from domain.errors import ExternalServiceError

    monkeypatch.setattr(
        "api.routes.predict.run_predict",
        lambda cmd: (_ for _ in ()).throw(
            ExternalServiceError(
                code="LABEL_STUDIO_WRITE_FAILED",
                message="Could not write predictions to Label Studio.",
            )
        ),
    )
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 502
    assert res.get_json()["error"] == "LABEL_STUDIO_WRITE_FAILED"


# --- 500 response contract violated ---


def test_predict_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.predict.run_predict",
        lambda cmd: {"wrong_field": "oops"},
    )
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 500
    assert res.get_json()["error"] == "RESPONSE_CONTRACT_VIOLATED"


# --- health ---


def test_health_returns_200(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"
