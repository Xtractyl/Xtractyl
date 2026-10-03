# worker/tests/unit/test_worker.py
from unittest.mock import patch

import pytest
from contracts.jobs import JobPayload
from pydantic import ValidationError

# --- Fixtures ---


@pytest.fixture
def valid_payload():
    return {
        "job_id": "123",
        "project_name": "test_project",
        "label_studio_id": 99,
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


def test_handle_job_sends_failed_callback_on_exception(valid_job):
    import app as worker_app

    with (
        patch("app.prelabel_project", side_effect=Exception("boom")),
        patch("app._send_callback") as send_callback,
    ):
        worker_app.handle_job(valid_job)

    send_callback.assert_called_once_with("123", "failed", error="boom")


def test_handle_job_sends_done_callback(valid_job):
    import app as worker_app

    with (
        patch("app.prelabel_project", return_value=False),
        patch("app._send_callback") as send_callback,
    ):
        worker_app.handle_job(valid_job)

    send_callback.assert_called_once_with("123", "done")


def test_handle_job_sends_cancelled_callback_when_stopped(valid_job):
    import app as worker_app

    with (
        patch("app.prelabel_project", return_value=True),
        patch("app._send_callback") as send_callback,
    ):
        worker_app.handle_job(valid_job)

    send_callback.assert_called_once_with("123", "cancelled")
