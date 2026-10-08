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
        "task_filenames": ["a.html"],
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


# --- run_job ---


def test_run_job_reports_failure_to_orchestrator(valid_job):
    from domain.jobs import run_job

    with (
        patch("domain.jobs.prelabel_project", side_effect=Exception("boom")),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_called_once_with(valid_job.job_id, "boom")


def test_run_job_reports_nothing_on_success(valid_job):
    from domain.jobs import run_job

    with (
        patch("domain.jobs.prelabel_project", return_value=None),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_not_called()
