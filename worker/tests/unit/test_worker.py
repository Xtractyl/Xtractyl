# worker/tests/unit/test_worker.py
from unittest.mock import MagicMock, patch

import pytest
from contracts.jobs import JobPayload
from domain.errors import ExternalServiceError, NotFound
from pydantic import ValidationError

# --- Fixtures ---


@pytest.fixture
def valid_payload():
    return {
        "job_id": "123",
        "project_name": "test_project",
        "model": "llama3.1:8b",
        "system_prompt": "You are a helpful assistant.",
        "token": "abc123token",
        "questions_and_labels": {
            "questions": ["Q1"],
            "labels": ["L1"],
        },
    }


@pytest.fixture
def valid_job(valid_payload):
    return JobPayload.model_validate(valid_payload)


# --- Contract ---


def test_job_payload_valid(valid_payload):
    job = JobPayload.model_validate(valid_payload)
    assert job.job_id == "123"
    assert job.questions_and_labels.questions == ["Q1"]


def test_job_payload_missing_token_raises(valid_payload):
    del valid_payload["token"]
    with pytest.raises(ValidationError):
        JobPayload.model_validate(valid_payload)


def test_job_payload_missing_questions_raises(valid_payload):
    valid_payload["questions_and_labels"] = {"questions": [], "labels": ["L1"]}
    with pytest.raises(ValidationError):
        JobPayload.model_validate(valid_payload)


def test_job_payload_missing_job_id_raises(valid_payload):
    del valid_payload["job_id"]
    with pytest.raises(ValidationError):
        JobPayload.model_validate(valid_payload)


# --- handle_job ---


def test_handle_job_sets_running_and_succeeded(valid_job):
    import app as worker_app

    mock_r = MagicMock()
    mock_r.hget.return_value = "RUNNING"

    with (
        patch.object(worker_app, "r", mock_r),
        patch("app.prelabel_project", return_value=["log1", "log2"]),
    ):
        worker_app.handle_job(valid_job)

    calls = [str(c) for c in mock_r.hset.call_args_list]
    assert any("RUNNING" in c for c in calls)
    assert any("SUCCEEDED" in c for c in calls)


def test_handle_job_sets_failed_on_exception(valid_job):
    import app as worker_app

    mock_r = MagicMock()
    mock_r.hget.return_value = "RUNNING"

    with (
        patch.object(worker_app, "r", mock_r),
        patch("app.prelabel_project", side_effect=Exception("boom")),
    ):
        worker_app.handle_job(valid_job)

    calls = [str(c) for c in mock_r.hset.call_args_list]
    assert any("FAILED" in c for c in calls)


def test_handle_job_sets_cancelled_when_cancel_requested(valid_job):
    import app as worker_app

    mock_r = MagicMock()
    mock_r.hget.return_value = "CANCEL_REQUESTED"

    with (
        patch.object(worker_app, "r", mock_r),
        patch("app.prelabel_project", return_value=[]),
    ):
        worker_app.handle_job(valid_job)

    calls = [str(c) for c in mock_r.hset.call_args_list]
    assert any("CANCELLED" in c for c in calls)


# --- resolve_project_id ---


def test_resolve_project_id_401_raises_external_service_error():
    from infrastructure.label_studio import resolve_project_id
    from requests.exceptions import HTTPError

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

    with patch("infrastructure.label_studio.requests.get", return_value=mock_response):
        with pytest.raises(ExternalServiceError) as exc:
            resolve_project_id("bad_token", "my_project")
        assert exc.value.code == "LABEL_STUDIO_UNAUTHORIZED"


def test_resolve_project_id_not_found_raises_not_found():
    from infrastructure.label_studio import resolve_project_id

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"results": [], "next": None}

    with patch("infrastructure.label_studio.requests.get", return_value=mock_response):
        with pytest.raises(NotFound) as exc:
            resolve_project_id("good_token", "nonexistent_project")
        assert exc.value.code == "PROJECT_NOT_FOUND"


def test_resolve_project_id_returns_id():
    from infrastructure.label_studio import resolve_project_id

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "results": [{"title": "my_project", "id": 42}],
        "next": None,
    }

    with patch("infrastructure.label_studio.requests.get", return_value=mock_response):
        project_id = resolve_project_id("good_token", "my_project")
    assert project_id == 42
