# ml_backend/domain/predict.py
from __future__ import annotations

from bs4 import BeautifulSoup
from infrastructure.label_studio import save_predictions_to_labelstudio
from infrastructure.ollama import ask_llm_with_timeout

from domain.errors import ExternalServiceError, InternalError
from domain.models.predict import PredictCommand
from domain.utils.dom_extract import extract_dom_with_chromium
from domain.utils.dom_match import extract_xpath_matches_from_dom
from domain.utils.perf_collector import PerfCollector


def run_predict(cmd: PredictCommand) -> dict:
    perf = PerfCollector()
    llm = cmd.llm_config
    ls = cmd.label_studio_config
    qal = cmd.questions_and_labels

    with perf.measure("dom.extract"):
        try:
            dom_data = extract_dom_with_chromium(cmd.html)
        except Exception as e:
            raise InternalError(
                code="DOM_EXTRACT_FAILED",
                message="Failed to extract DOM from HTML.",
                meta={"error": str(e)},
            )

    puretext = BeautifulSoup(cmd.html, "html.parser").get_text("\n", strip=True)

    answers_by_label: dict = {}

    for q, lab in zip(qal.questions, qal.labels, strict=False):
        prompt = f"{llm.system_prompt}\n\nQuestion: {q}\n\nText: {puretext}"
        with perf.measure("llm.call", label=str(lab)):
            try:
                answer = ask_llm_with_timeout(prompt=prompt, model_name=llm.ollama_model)
            except ExternalServiceError as e:
                # one failed question fails the whole task, the error is passed on unchanged
                e.meta = {**(e.meta or {}), "label": str(lab)}
                raise
        answers_by_label[str(lab)] = {
            "question": q,
            "answer": answer,
            "status": "ok",
            "error": None,
        }

    with perf.measure("dom.match"):
        try:
            answers_list = [
                {"label": lab, "question": v.get("question"), "answer": v.get("answer")}
                for lab, v in answers_by_label.items()
            ]
            prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers_list)

            diag_labels = {
                d.get("label")
                for d in (diagnostics or [])
                if isinstance(d, dict) and d.get("label")
            }

            dom_match_by_label = {}
            for lab, v in answers_by_label.items():
                if not v.get("answer"):
                    dom_match_by_label[lab] = None
                else:
                    dom_match_by_label[lab] = lab not in diag_labels

        except Exception as e:
            raise InternalError(
                code="DOM_MATCH_FAILED",
                message="Unexpected error while matching answers into the DOM (not a 'not found' case).",
                meta={"error": str(e)},
            )

    save_predictions_to_labelstudio(
        token=ls.ls_token,
        model_version=llm.ollama_model,
        task_id=cmd.task_id,
        prediction_result=prelabels,
    )

    return {
        "model_version": llm.ollama_model,
        "score": 1.0 if prelabels else 0.0,
        "result": prelabels,
        "meta": {
            "predictions": prelabels,
            "raw_llm_answers": answers_by_label,
            "dom_match_diagnostics": diagnostics,
            "dom_match_by_label": dom_match_by_label,
            **perf.to_dict()["request"],
        },
    }
