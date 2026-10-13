# worker/tests/unit/test_ml_backend.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from contracts.jobs import JobPayload
from domain.errors import ContractViolation, ExternalServiceError


@pytest.fixture
def job():
    return JobPayload.model_validate(
        {
            "job_id": "123",
            "project_name": "p",
            "label_studio_id": 1,
            "model": "llama3.1:8b",
            "system_prompt": "Extract.",
            "token": "secret-token",
            "questions_and_labels": {"questions": ["Q1"], "labels": ["L1"]},
            "task_filenames": ["a.html"],
        }
    )


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
    "n_timeouts": 0,
    "avg_llm_call_ms": 1.0,
    "median_llm_call_ms": 1.0,
}


def _response(status=200, json_body=None, text="", json_error=False):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_error:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = json_body
    return resp


def _predict(job, html="<p>x</p>"):
    from infrastructure.ml_backend import predict

    return predict(task_id=5, html=html, filename="a.html", job=job)


def test_predict_returns_meta(job):
    body = {"model_version": "m", "score": 1.0, "result": [], "meta": {**META, "extra": 1}}
    with patch("infrastructure.ml_backend.requests.post", return_value=_response(200, body)):
        meta = _predict(job)
    assert meta.n_llm_calls == 1


def test_predict_sends_no_infrastructure_config(job):
    body = {"model_version": "m", "score": 1.0, "result": [], "meta": META}
    with patch(
        "infrastructure.ml_backend.requests.post", return_value=_response(200, body)
    ) as post:
        _predict(job)
    sent = post.call_args.kwargs["json"]
    assert sent["llm_config"] == {"ollama_model": "llama3.1:8b", "system_prompt": "Extract."}
    assert sent["label_studio_config"] == {"ls_token": "secret-token"}


def test_predict_without_html_is_a_contract_violation_without_input(job):
    with patch("infrastructure.ml_backend.requests.post") as post:
        with pytest.raises(ContractViolation) as exc:
            _predict(job, html=None)
    post.assert_not_called()
    assert exc.value.code == "ML_REQUEST_INVALID"
    assert "secret-token" not in str(exc.value.meta)


def test_predict_connection_error_is_unavailable(job):
    with patch(
        "infrastructure.ml_backend.requests.post", side_effect=requests.ConnectionError("down")
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _predict(job)
    assert exc.value.code == "ML_BACKEND_UNAVAILABLE"


def test_predict_timeout_is_its_own_code(job):
    with patch("infrastructure.ml_backend.requests.post", side_effect=requests.ReadTimeout("slow")):
        with pytest.raises(ExternalServiceError) as exc:
            _predict(job)
    assert exc.value.code == "ML_BACKEND_TIMEOUT"


def test_predict_takes_over_the_error_code_of_the_ml_backend(job):
    body = {"error": "LLM_TIMEOUT", "message": "The LLM did not answer in time."}
    with patch("infrastructure.ml_backend.requests.post", return_value=_response(502, body)):
        with pytest.raises(ExternalServiceError) as exc:
            _predict(job)
    assert exc.value.code == "LLM_TIMEOUT"
    assert str(exc.value) == "[LLM_TIMEOUT] The LLM did not answer in time."


def test_predict_error_without_readable_body_falls_back_to_http_code(job):
    with patch(
        "infrastructure.ml_backend.requests.post",
        return_value=_response(500, text="<html>oops</html>", json_error=True),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _predict(job)
    assert exc.value.code == "ML_BACKEND_HTTP_ERROR"
    assert exc.value.meta["status"] == 500


def test_predict_answer_that_is_not_json_is_a_contract_violation(job):
    with patch(
        "infrastructure.ml_backend.requests.post", return_value=_response(200, json_error=True)
    ):
        with pytest.raises(ContractViolation) as exc:
            _predict(job)
    assert exc.value.code == "ML_RESPONSE_INVALID"


def test_predict_answer_with_missing_meta_field_is_a_contract_violation(job):
    meta = {k: v for k, v in META.items() if k != "n_timeouts"}
    body = {"model_version": "m", "score": 1.0, "result": [], "meta": meta}
    with patch("infrastructure.ml_backend.requests.post", return_value=_response(200, body)):
        with pytest.raises(ContractViolation) as exc:
            _predict(job)
    assert exc.value.code == "ML_RESPONSE_INVALID"
    assert exc.value.meta["errors"][0]["loc"] == ["meta", "n_timeouts"]
