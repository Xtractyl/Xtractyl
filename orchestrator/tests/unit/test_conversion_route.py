# orchestrator/tests/unit/test_conversion_route.py
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- conversion/prepare ---


def test_conversion_prepare_missing_fields_returns_422(client):
    res = client.post("/conversion/prepare", json={})
    assert res.status_code == 422


def test_conversion_prepare_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.prepare_conversion",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.post("/conversion/prepare", json={"project": "my_project", "filenames": ["a.pdf"]})
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_prepare_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.prepare_conversion",
        lambda cmd, **kwargs: {
            "job_id": 1,
            "presigned_urls": [
                {"filename": "a.pdf", "upload_url": "https://x", "pdf_key": "p/a.pdf"}
            ],
        },
    )
    res = client.post("/conversion/prepare", json={"project": "my_project", "filenames": ["a.pdf"]})
    assert res.status_code == 200
    data = res.get_json()
    assert data["job_id"] == 1


# --- conversion/convert ---


def test_conversion_convert_missing_fields_returns_422(client):
    res = client.post("/conversion/convert", json={})
    assert res.status_code == 422


def test_conversion_convert_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.start_conversion",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.post("/conversion/convert", json={"job_id": 1})
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_convert_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.start_conversion",
        lambda cmd, **kwargs: {"job_id": 1, "status": "converting"},
    )
    res = client.post("/conversion/convert", json={"job_id": 1})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "converting"


# --- conversion/cancel ---


def test_conversion_cancel_missing_fields_returns_422(client):
    res = client.post("/conversion/cancel", json={})
    assert res.status_code == 422


def test_conversion_cancel_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.cancel_conversion",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.post("/conversion/cancel", json={"job_id": 1})
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_cancel_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.cancel_conversion",
        lambda cmd, **kwargs: {"job_id": 1, "status": "cancelled"},
    )
    res = client.post("/conversion/cancel", json={"job_id": 1})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "cancelled"


# --- conversion/discard ---


def test_conversion_discard_missing_fields_returns_422(client):
    res = client.post("/conversion/discard", json={})
    assert res.status_code == 422


def test_conversion_discard_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.discard_conversion",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.post("/conversion/discard", json={"job_id": 1})
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_discard_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.discard_conversion",
        lambda cmd, **kwargs: {"status": "discarded"},
    )
    res = client.post("/conversion/discard", json={"job_id": 1})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "discarded"


# --- conversion/status ---


def test_conversion_status_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.get_conversion_status",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.get("/conversion/status/1")
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_status_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.get_conversion_status",
        lambda cmd, **kwargs: {
            "job_id": 1,
            "status": "converting",
            "total_files": 2,
            "converted_files": 1,
            "error": None,
        },
    )
    res = client.get("/conversion/status/1")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "converting"


# --- conversion/callback ---


def test_conversion_callback_missing_fields_returns_422(client):
    res = client.post("/conversion/callback", json={})
    assert res.status_code == 422


def test_conversion_callback_contract_violated_returns_500(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.handle_conversion_callback",
        lambda cmd, **kwargs: {"wrong_field": "oops"},
    )
    res = client.post(
        "/conversion/callback",
        json={"job_id": 1, "filename": "a.pdf", "html_key": "k", "success": True},
    )
    assert res.status_code == 500
    data = res.get_json()
    assert data["error"] == "RESPONSE_CONTRACT_VIOLATED"


def test_conversion_callback_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.conversion.handle_conversion_callback",
        lambda cmd, **kwargs: {"status": "ok"},
    )
    res = client.post(
        "/conversion/callback",
        json={"job_id": 1, "filename": "a.pdf", "html_key": "k", "success": True},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
