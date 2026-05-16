# ml_backend/domain/predict.py
from __future__ import annotations

from bs4 import BeautifulSoup
from domain.errors import ExternalServiceError, InternalError
from domain.models.predict import PredictCommand
from infrastructure.label_studio import attach_meta_to_task, save_predictions_to_labelstudio
from utils.client import ask_llm_with_timeout
from utils.dom_extract import extract_dom_with_chromium
from utils.dom_match import extract_xpath_matches_from_dom
from utils.perf_collector import PerfCollector


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
    timed_out = False

    for q, lab in zip(qal.questions, qal.labels, strict=False):
        prompt = f"{llm.system_prompt}\n\nQuestion: {q}\n\nText: {puretext}"
        with perf.measure("llm.call", label=str(lab)) as t:
            result = ask_llm_with_timeout(
                ollama_base=llm.ollama_base,
                prompt=prompt,
                timeout=llm.llm_timeout_seconds,
                model_name=llm.ollama_model,
            )
            t["status"] = result.get("status")
            if result.get("status") == "timeout":
                timed_out = True
            answers_by_label[str(lab)] = {
                "question": q,
                "answer": result["answer"],
                "status": result["status"],
                "error": result.get("error"),
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
                status = v.get("status")
                ans = v.get("answer")
                if status != "ok" or not ans:
                    dom_match_by_label[lab] = None
                else:
                    dom_match_by_label[lab] = lab not in diag_labels

        except Exception as e:
            prelabels, diagnostics = [], [{"reason": "match_failed", "error": str(e)}]
            dom_match_by_label = {}

    meta = {
        "raw_llm_answers": answers_by_label,
        "system_prompt": llm.system_prompt,
        "model": llm.ollama_model,
        "dom_match_diagnostics": diagnostics,
        "dom_match_by_label": dom_match_by_label,
        "job_id": cmd.job_id,
        "performance": perf.to_dict(include_events=True),
    }

    try:
        save_predictions_to_labelstudio(
            label_studio_url=ls.label_studio_url,
            token=ls.ls_token,
            model_version=llm.ollama_model,
            task_id=cmd.task_id,
            prediction_result=prelabels,
        )
        attach_meta_to_task(
            label_studio_url=ls.label_studio_url,
            token=ls.ls_token,
            task_id=int(cmd.task_id),
            meta=meta,
        )
    except Exception as e:
        raise ExternalServiceError(
            code="LABEL_STUDIO_WRITE_FAILED",
            message="Failed to write predictions to Label Studio.",
            meta={"error": str(e)},
        )

    return {
        "model_version": llm.ollama_model,
        "score": 1.0 if prelabels else 0.0,
        "result": prelabels,
        "meta": {
            **meta,
            "status": "timeout" if timed_out else "success",
            "task_id": cmd.task_id,
            "job_id": cmd.job_id,
        },
    }
