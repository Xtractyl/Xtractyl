# worker/tests/unit/test_worker.py
from unittest.mock import patch

import pytest
from contracts.jobs import JobPayload
from domain.errors import ExternalServiceError
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


def test_run_job_reports_domain_error_with_code_to_orchestrator(valid_job):
    from domain.jobs import run_job

    error = ExternalServiceError(code="LABEL_STUDIO_UNAUTHORIZED", message="Token is invalid.")
    with (
        patch("domain.jobs.prelabel_project", side_effect=error),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_called_once_with(
        valid_job.job_id, "[LABEL_STUDIO_UNAUTHORIZED] Token is invalid."
    )


def test_run_job_hides_details_of_unexpected_errors(valid_job):
    from domain.jobs import run_job

    with (
        patch("domain.jobs.prelabel_project", side_effect=Exception("secret detail")),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_called_once_with(
        valid_job.job_id, "[INTERNAL_ERROR] Unexpected error in the worker."
    )


def test_run_job_does_not_report_to_an_unavailable_orchestrator(valid_job):
    from domain.jobs import run_job

    error = ExternalServiceError(code="ORCHESTRATOR_UNAVAILABLE", message="Orchestrator is down.")
    with (
        patch("domain.jobs.prelabel_project", side_effect=error),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_not_called()


# --- invalid payload in the queue ---


def test_extract_job_id():
    from app import _extract_job_id

    assert _extract_job_id('{"job_id": "7"}') == "7"
    assert _extract_job_id('{"job_id": 7}') == "7"
    assert _extract_job_id('{"job_id": ""}') is None
    assert _extract_job_id('{"other": 1}') is None
    assert _extract_job_id("[1, 2]") is None
    assert _extract_job_id("not json") is None


def test_invalid_payload_with_job_id_fails_the_run_without_message():
    from app import _handle_invalid_payload

    with patch("app.send_job_failed") as report:
        _handle_invalid_payload('{"job_id": "7"}', ValueError("bad"))

    report.assert_called_once_with("7", None)


def test_invalid_payload_without_job_id_reports_nothing():
    from app import _handle_invalid_payload

    with patch("app.send_job_failed") as report:
        _handle_invalid_payload("not json", ValueError("bad"))

    report.assert_not_called()


def test_run_job_reports_nothing_on_success(valid_job):
    from domain.jobs import run_job

    with (
        patch("domain.jobs.prelabel_project", return_value=None),
        patch("domain.jobs.send_job_failed") as report,
    ):
        run_job(valid_job)

    report.assert_not_called()
