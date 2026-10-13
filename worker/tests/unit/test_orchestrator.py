# worker/tests/unit/test_orchestrator.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from domain.errors import ContractViolation, ExternalServiceError

META = {
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


def _response(status=200, json_body=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.json.return_value = json_body
    return resp


def _send(**overrides):
    from infrastructure.orchestrator import send_task_result

    args = {
        "job_id": "1",
        "task_id": 5,
        "filename": "a.html",
        "success": True,
        "error": None,
        "result": META,
    }
    args.update(overrides)
    return send_task_result(**args)


@pytest.fixture(autouse=True)
def no_sleep():
    with patch("infrastructure.orchestrator.time.sleep") as sleep:
        yield sleep


def test_task_result_returns_continue_flag():
    with patch(
        "infrastructure.orchestrator.requests.post",
        return_value=_response(200, {"continue": False}),
    ):
        assert _send() is False


def test_unreachable_orchestrator_is_retried_with_growing_pauses(no_sleep):
    with patch(
        "infrastructure.orchestrator.requests.post",
        side_effect=[
            requests.ConnectionError("down"),
            requests.ConnectionError("down"),
            _response(200, {"continue": True}),
        ],
    ) as post:
        assert _send() is True
    assert post.call_count == 3
    assert [c.args[0] for c in no_sleep.call_args_list] == [10.0, 20.0]


def test_orchestrator_stays_unreachable(no_sleep):
    with patch(
        "infrastructure.orchestrator.requests.post", side_effect=requests.ConnectionError("down")
    ) as post:
        with pytest.raises(ExternalServiceError) as exc:
            _send()
    assert exc.value.code == "ORCHESTRATOR_UNAVAILABLE"
    assert post.call_count == 5
    assert no_sleep.call_count == 4


def test_rejected_task_result_is_not_retried():
    with patch(
        "infrastructure.orchestrator.requests.post", return_value=_response(409, text="mismatch")
    ) as post:
        with pytest.raises(ExternalServiceError) as exc:
            _send()
    assert post.call_count == 1
    assert exc.value.code == "TASK_RESULT_REJECTED"
    assert exc.value.meta == {"status": 409, "body": "mismatch"}


def test_task_result_that_breaks_the_contract_is_not_sent():
    with patch("infrastructure.orchestrator.requests.post") as post:
        with pytest.raises(ContractViolation) as exc:
            _send(success=True, error=None, result=None)
    post.assert_not_called()
    assert exc.value.code == "TASK_RESULT_INVALID"


def test_failed_task_result_needs_an_error():
    with patch("infrastructure.orchestrator.requests.post") as post:
        with pytest.raises(ContractViolation):
            _send(success=False, error=None, result=None)
    post.assert_not_called()


def test_answer_without_continue_is_a_contract_violation():
    with patch("infrastructure.orchestrator.requests.post", return_value=_response(200, {})):
        with pytest.raises(ContractViolation) as exc:
            _send()
    assert exc.value.code == "ORCHESTRATOR_RESPONSE_INVALID"


def test_send_job_failed_never_raises_when_orchestrator_is_down():
    from infrastructure.orchestrator import send_job_failed

    with patch(
        "infrastructure.orchestrator.requests.post", side_effect=requests.ConnectionError("down")
    ):
        send_job_failed("1", "[X] y")


def test_send_job_failed_sends_run_id_and_error():
    from infrastructure.orchestrator import send_job_failed

    with patch(
        "infrastructure.orchestrator.requests.post", return_value=_response(200, {"status": "ok"})
    ) as post:
        send_job_failed("1", None)
    assert post.call_args.kwargs["json"] == {"job_id": "1", "error": None}
