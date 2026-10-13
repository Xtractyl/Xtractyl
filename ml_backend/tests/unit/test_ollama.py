# ml_backend/tests/unit/test_ollama.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from domain.errors import ExternalServiceError
from infrastructure.ollama import ask_llm_with_timeout


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


def _ask():
    return ask_llm_with_timeout(prompt="p", model_name="m")


def test_returns_the_stripped_answer():
    with patch(
        "infrastructure.ollama.requests.post", return_value=_response(body={"response": " yes \n"})
    ):
        assert _ask() == "yes"


def test_empty_answer_is_none_not_an_error():
    with patch(
        "infrastructure.ollama.requests.post", return_value=_response(body={"response": "  "})
    ):
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
