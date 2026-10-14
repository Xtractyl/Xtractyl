# ml_backend/tests/unit/test_ollama.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from domain.errors import ExternalServiceError
from infrastructure.ollama import PROMPT_TOKEN_LIMIT, ask_llm_with_timeout


def _response(status_code=200, body=None, json_error=False):
    resp = MagicMock()
    resp.status_code = status_code
    if json_error:
        resp.json.side_effect = ValueError("not json")
    else:
        resp.json.return_value = body if body is not None else {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status_code}")
    return resp


def _ok(response="yes", prompt_tokens=100):
    return _response(body={"response": response, "prompt_eval_count": prompt_tokens})


def _ask():
    return ask_llm_with_timeout(prompt="p", model_name="m")


def test_returns_the_stripped_answer():
    with patch("infrastructure.ollama.requests.post", return_value=_ok(" yes \n")):
        assert _ask() == "yes"


def test_empty_answer_is_none_not_an_error():
    with patch("infrastructure.ollama.requests.post", return_value=_ok("  ")):
        assert _ask() is None


def test_404_is_model_missing():
    with patch("infrastructure.ollama.requests.post", return_value=_response(404)):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_MODEL_MISSING"
    assert exc.value.meta == {"model": "m"}


def test_timeout_is_llm_timeout():
    with patch("infrastructure.ollama.requests.post", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_TIMEOUT"


def test_connection_error_is_llm_call_failed():
    with patch(
        "infrastructure.ollama.requests.post",
        side_effect=requests.exceptions.ConnectionError("down"),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_CALL_FAILED"


def test_http_error_is_llm_call_failed():
    with patch("infrastructure.ollama.requests.post", return_value=_response(500)):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_CALL_FAILED"


def test_answer_that_is_not_json_is_llm_call_failed():
    with patch("infrastructure.ollama.requests.post", return_value=_response(json_error=True)):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_CALL_FAILED"


def test_prompt_below_the_limit_is_fine():
    with patch(
        "infrastructure.ollama.requests.post",
        return_value=_ok(prompt_tokens=PROMPT_TOKEN_LIMIT - 1),
    ):
        assert _ask() == "yes"


def test_prompt_at_the_limit_is_context_exceeded():
    with patch(
        "infrastructure.ollama.requests.post",
        return_value=_ok(prompt_tokens=PROMPT_TOKEN_LIMIT),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_CONTEXT_EXCEEDED"
    assert exc.value.meta == {
        "model": "m",
        "prompt_tokens": PROMPT_TOKEN_LIMIT,
        "limit": PROMPT_TOKEN_LIMIT,
    }


def test_context_exceeded_wins_over_an_empty_answer():
    with patch(
        "infrastructure.ollama.requests.post",
        return_value=_ok(response="", prompt_tokens=PROMPT_TOKEN_LIMIT),
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_CONTEXT_EXCEEDED"


def test_missing_prompt_eval_count_is_llm_response_invalid():
    with patch(
        "infrastructure.ollama.requests.post", return_value=_response(body={"response": "yes"})
    ):
        with pytest.raises(ExternalServiceError) as exc:
            _ask()
    assert exc.value.code == "LLM_RESPONSE_INVALID"
    assert exc.value.meta == {"model": "m"}
