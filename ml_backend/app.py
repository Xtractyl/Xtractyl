# /ml_backend/app.py
import os

from bs4 import BeautifulSoup
from client import ask_llm_with_timeout
from dom_extract import extract_dom_with_chromium
from dom_match import extract_xpath_matches_from_dom
from flask import Flask, jsonify, request
from flask_cors import CORS
from label_studio import attach_meta_to_task, save_predictions_to_labelstudio
from perf_collector import PerfCollector

PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))

app = Flask(__name__)

FRONTEND_ORIGIN = f"http://localhost:{int(os.getenv('FRONTEND_PORT', '5173'))}"
LABELSTUDIO_ORIGIN = f"http://localhost:{int(os.getenv('LABELSTUDIO_PORT', '8080'))}"

CORS(
    app,
    resources={r"/*": {"origins": [FRONTEND_ORIGIN, LABELSTUDIO_ORIGIN]}},
    supports_credentials=True,
)


# ----------------------------------
# Routes
# ----------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    perf = PerfCollector()
    # robust JSON-Parsing
    data = request.get_json(silent=True) or {}
    params = data.get("config") or data.get("params") or {}

    # Job / Log-paths (best effort)
    job_id = (
        request.headers.get("X-Prelabel-Job")
        or request.args.get("job_id")
        or data.get("job_id")
        or "no-job"
    )

    # Task-Objekt
    task_obj = data.get("task") or (data.get("tasks") or [{}])[0]
    task_id = (
        task_obj.get("id")
        or task_obj.get("pk")
        or task_obj.get("task_id")
        or data.get("task_id")
        or data.get("id")
        or "unknown-task"
    )

    # HTML from task.data[...] or top level
    html_content = ""
    d = task_obj.get("data") or data.get("data") or {}
    for k in ("html", "text", "content", "raw"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            html_content = v
            break
    if not html_content:
        for k in ("html", "text", "content", "raw"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                html_content = v
                break
    if not html_content:
        return jsonify(
            {
                "model_version": params.get("ollama_model", "stub"),
                "score": 0.0,
                "result": [],
                "meta": {
                    "raw_llm_answers": {},
                    "system_prompt": params.get("system_prompt"),
                    "model": params.get("ollama_model"),
                    "dom_match_diagnostics": [{"reason": "HTML content missing"}],
                    "dom_match_ok": False,
                    "status": "error",
                    "task_id": task_id,
                    "job_id": job_id,
                },
            }
        ), 200

    # DOM
    with perf.measure("dom.extract"):
        dom_data = extract_dom_with_chromium(html_content)

    # Q&L (optional – kein 400, wenn fehlt)
    qa_config = data.get("questions_and_labels") or {}
    questions = qa_config.get("questions") or []
    labels = qa_config.get("labels") or []

    # LLM only if config is complete + Q&L
    answers_by_label = {}
    timed_out = False

    have_llm_cfg = all(
        k in params for k in ("ollama_model", "ollama_base", "system_prompt", "llm_timeout_seconds")
    )
    if have_llm_cfg and questions and labels:
        puretext = BeautifulSoup(html_content or "", "html.parser").get_text("\n", strip=True)

        for q, lab in zip(questions, labels, strict=False):
            prompt = f"{params['system_prompt']}\n\nQuestion: {q}\n\nText: {puretext}"
            with perf.measure("llm.call", label=str(lab)) as t:
                llm = ask_llm_with_timeout(
                    params,
                    prompt,
                    timeout=int(params["llm_timeout_seconds"]),
                    model_name=params["ollama_model"],
                )
                t["status"] = llm.get("status")
                if llm.get("status") == "timeout":
                    timed_out = True
                answers_by_label[str(lab)] = {
                    "question": q,
                    "answer": llm["answer"],  # str|None
                    "status": llm["status"],  # ok|timeout|error|model_missing
                    "error": llm.get("error"),
                }

    with perf.measure("dom.match"):
        dom_match_by_label = {}
        try:
            answers_list = [
                {"label": lab, "question": v.get("question"), "answer": v.get("answer")}
                for lab, v in (answers_by_label or {}).items()
            ]
            prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers_list)

            diag_labels = {
                d.get("label")
                for d in (diagnostics or [])
                if isinstance(d, dict) and d.get("label")
            }

            dom_match_by_label = {}
            for lab, v in (answers_by_label or {}).items():
                status = (v or {}).get("status")
                ans = (v or {}).get("answer")

                if status != "ok" or not ans:
                    dom_match_by_label[lab] = None
                else:
                    dom_match_by_label[lab] = lab not in diag_labels

        except Exception as e:
            prelabels, diagnostics = [], [{"reason": "match_failed", "error": str(e)}]
            dom_match_by_label = {}

    meta = {
        "raw_llm_answers": answers_by_label,
        "system_prompt": params.get("system_prompt"),
        "model": params.get("ollama_model"),
        "dom_match_diagnostics": diagnostics,
        "dom_match_by_label": dom_match_by_label,
        "job_id": job_id,
        "performance": perf.to_dict(include_events=True),
    }

    if all(k in params for k in ("label_studio_url", "ls_token")):
        try:
            save_predictions_to_labelstudio(params, task_id, prelabels)  # ohne meta
            attach_meta_to_task(params, int(task_id), meta)
        except Exception:
            pass

    return jsonify(
        {
            "model_version": params.get("ollama_model", "stub"),
            "score": 1.0 if prelabels else 0.0,
            "result": prelabels,
            "meta": {
                **meta,
                "status": "timeout" if timed_out else "success",
                "task_id": task_id,
                "job_id": job_id,
            },
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# required from label studio for registration
@app.route("/setup", methods=["GET", "POST"])
def setup():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
