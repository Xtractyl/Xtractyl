# worker/tests/unit/test_prelabel_project.py
from unittest.mock import patch

import pytest
from contracts.jobs import JobPayload
from contracts.ml_backend import PredictMeta
from domain.errors import ContractViolation, ExternalServiceError, InvalidState

META = PredictMeta.model_validate(
    {
        "predictions": [],
        "raw_llm_answers": {},
        "dom_match_diagnostics": [],
        "dom_match_by_label": {},
        "task_ms_total": 1.0,
        "task_ms_llm_total": 1.0,
        "task_ms_dom_extract": 1.0,
        "task_ms_dom_match": 1.0,
        "n_llm_calls": 1,
        "avg_llm_call_ms": 1.0,
        "median_llm_call_ms": 1.0,
    }
)


@pytest.fixture
def job():
    return JobPayload.model_validate(
        {
            "job_id": "123",
            "project_name": "p",
            "label_studio_id": 1,
            "model": "llama3.1:8b",
            "system_prompt": "Extract.",
            "token": "t",
            "questions_and_labels": {"questions": ["Q1"], "labels": ["L1"]},
            "task_filenames": ["a.html", "b.html"],
        }
    )


def _tasks():
    return [
        {"id": 1, "data": {"name": "a.html", "html": "<p>a</p>"}},
        {"id": 2, "data": {"name": "b.html", "html": "<p>b</p>"}},
    ]


def _run(job, tasks, predict, send):
    from domain.prelabel_project import prelabel_project

    with (
        patch("domain.prelabel_project.get_tasks_without_predictions", return_value=tasks),
        patch("domain.prelabel_project.predict", side_effect=predict),
        patch("domain.prelabel_project.send_task_result", side_effect=send) as send_mock,
    ):
        prelabel_project(job)
    return send_mock


def test_successful_tasks_are_reported_with_their_result(job):
    send = _run(job, _tasks(), predict=[META, META], send=[True, True])

    assert send.call_count == 2
    first = send.call_args_list[0].kwargs
    assert first["success"] is True and first["error"] is None
    assert first["result"]["n_llm_calls"] == 1


def test_a_failing_task_fails_only_that_task(job):
    error = ExternalServiceError(code="ML_BACKEND_TIMEOUT", message="ML backend did not answer.")
    send = _run(job, _tasks(), predict=[error, META], send=[True, True])

    first, second = (c.kwargs for c in send.call_args_list)
    assert first["success"] is False
    assert first["error"] == "[ML_BACKEND_TIMEOUT] ML backend did not answer."
    assert first["result"] is None
    assert second["success"] is True


def test_a_contract_violation_fails_only_that_task(job):
    error = ContractViolation(code="ML_RESPONSE_INVALID", message="Bad answer.")
    send = _run(job, _tasks(), predict=[error, META], send=[True, True])

    assert send.call_args_list[0].kwargs["error"] == "[ML_RESPONSE_INVALID] Bad answer."
    assert send.call_args_list[1].kwargs["success"] is True


def test_task_without_html_is_sent_to_predict_and_fails_there(job):
    tasks = [{"id": 1, "data": {"name": "a.html"}}, {"id": 2, "data": {"name": "b.html"}}]
    error = ContractViolation(code="ML_REQUEST_INVALID", message="Bad request.")
    send = _run(job, tasks, predict=[error, error], send=[True, True])

    assert send.call_count == 2
    assert send.call_args_list[0].kwargs["error"] == "[ML_REQUEST_INVALID] Bad request."


def test_cancelled_run_stops_after_the_current_task(job):
    send = _run(job, _tasks(), predict=[META, META], send=[False, True])

    assert send.call_count == 1


def test_error_while_reporting_a_task_ends_the_run(job):
    error = ExternalServiceError(code="TASK_RESULT_REJECTED", message="Rejected.")
    with pytest.raises(ExternalServiceError) as exc:
        _run(job, _tasks(), predict=[META, META], send=error)

    assert exc.value.code == "TASK_RESULT_REJECTED"


def test_out_of_sync_tasks_end_the_run_before_any_prediction(job):
    tasks = [{"id": 1, "data": {"name": "a.html", "html": "<p>a</p>"}}]
    with pytest.raises(InvalidState) as exc:
        _run(job, tasks, predict=[], send=[])

    assert exc.value.code == "TASKS_OUT_OF_SYNC"
    assert "b.html" in exc.value.message
