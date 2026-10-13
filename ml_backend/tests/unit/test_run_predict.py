# ml_backend/tests/unit/test_run_predict.py
import pytest
from api.contracts.predict import PredictMeta
from domain.errors import ExternalServiceError
from domain.models.predict import (
    LabelStudioConfig,
    LLMConfig,
    PredictCommand,
    QuestionsAndLabels,
)
from domain.predict import run_predict


@pytest.fixture
def cmd():
    return PredictCommand(
        job_id="1",
        task_id="42",
        filename="doc.html",
        html="<p>Some content</p>",
        questions_and_labels=QuestionsAndLabels(questions=["Q1", "Q2"], labels=["L1", "L2"]),
        llm_config=LLMConfig(ollama_model="m", system_prompt="s"),
        label_studio_config=LabelStudioConfig(ls_token="t"),
    )


@pytest.fixture
def saved(monkeypatch):
    calls = []
    monkeypatch.setattr("domain.predict.extract_dom_with_chromium", lambda html: [])
    monkeypatch.setattr(
        "domain.predict.extract_xpath_matches_from_dom",
        lambda dom, answers: ([{"from_name": "x"}], []),
    )
    monkeypatch.setattr(
        "domain.predict.save_predictions_to_labelstudio", lambda **kw: calls.append(kw)
    )
    return calls


def test_happy_path_returns_meta_that_matches_the_contract(cmd, saved, monkeypatch):
    monkeypatch.setattr("domain.predict.ask_llm_with_timeout", lambda prompt, model_name: "answer")
    result = run_predict(cmd)
    meta = PredictMeta.model_validate(result["meta"])
    assert meta.n_llm_calls == 2
    assert meta.dom_match_by_label == {"L1": True, "L2": True}
    assert meta.raw_llm_answers["L1"]["answer"] == "answer"
    assert len(saved) == 1


def test_empty_answer_has_no_dom_match(cmd, saved, monkeypatch):
    monkeypatch.setattr("domain.predict.ask_llm_with_timeout", lambda prompt, model_name: None)
    result = run_predict(cmd)
    assert result["meta"]["dom_match_by_label"] == {"L1": None, "L2": None}


def test_failed_question_fails_the_task_with_its_own_code_and_writes_nothing(
    cmd, saved, monkeypatch
):
    def fail(prompt, model_name):
        raise ExternalServiceError(code="LLM_TIMEOUT", message="The LLM did not answer in time.")

    monkeypatch.setattr("domain.predict.ask_llm_with_timeout", fail)
    with pytest.raises(ExternalServiceError) as exc:
        run_predict(cmd)
    assert exc.value.code == "LLM_TIMEOUT"
    assert exc.value.meta == {"label": "L1"}
    assert saved == []


def test_label_studio_error_is_not_wrapped_again(cmd, saved, monkeypatch):
    monkeypatch.setattr("domain.predict.ask_llm_with_timeout", lambda prompt, model_name: "a")

    def fail(**kw):
        raise ExternalServiceError(code="LABEL_STUDIO_UNREACHABLE", message="down")

    monkeypatch.setattr("domain.predict.save_predictions_to_labelstudio", fail)
    with pytest.raises(ExternalServiceError) as exc:
        run_predict(cmd)
    assert exc.value.code == "LABEL_STUDIO_UNREACHABLE"
