# /ml_backend/app.py
import json
import logging
import os
import pathlib

from bs4 import BeautifulSoup
from client import ask_llm_with_timeout
from dom_extract import extract_dom_with_chromium
from dom_match import extract_xpath_matches_from_dom
from flask import Flask, jsonify, request
from flask_cors import CORS
from label_studio import attach_meta_to_task, save_predictions_to_labelstudio
from logging_setup import attach_file_logger
from perf_collector import PerfCollector

# ----------------------------------
# Toggle for full DOM logging
# ----------------------------------
LOG_FULL_DOM = False  # <--- set to False to disable full DOM dump

# ----------------------------------
# Logging
# ----------------------------------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

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
# Central + per-job logging
# ----------------------------------
LOG_DIR = "/logs"
JOBS_DIR = os.path.join(LOG_DIR, "ml_backend_jobs")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

general_logfile = os.path.join(LOG_DIR, "ml_backend.log")
attach_file_logger(general_logfile)


def _job_log_paths(job_id: str | None):
    """Return per-job file paths; fall back to general files if job_id is None."""
    if job_id:
        base = os.path.join(JOBS_DIR, job_id)
        os.makedirs(base, exist_ok=True)
        return {
            "payload": os.path.join(base, "prediction_payload.log"),
            "timeouts": os.path.join(base, "timeout_tasks.log"),
            "dom_dump": os.path.join(base, "dom_dump.jsonl"),
        }
    else:
        return {
            "payload": os.path.join(LOG_DIR, "prediction_payload.log"),
            "timeouts": os.path.join(LOG_DIR, "timeout_tasks.log"),
            "dom_dump": os.path.join(LOG_DIR, "dom_dump.jsonl"),
        }


# ----------------------------------
# Routes
# ----------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    perf = PerfCollector()
    # robust JSON-Parsing
    data = request.get_json(silent=True) or {}
    params = data.get("config") or data.get("params") or {}

    # Job / Log-Pfade (best effort)
    job_id = (
        request.headers.get("X-Prelabel-Job")
        or request.args.get("job_id")
        or data.get("job_id")
        or "no-job"
    )
    job_paths = _job_log_paths(job_id)
    prediction_payload_path = job_paths["payload"]
    timeout_log_path = pathlib.Path(job_paths["timeouts"])
    dom_dump_path = pathlib.Path(job_paths["dom_dump"])

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

    # HTML aus task.data[...] oder Top-Level
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
    with perf.measure("dom_extract"):
        dom_data = extract_dom_with_chromium(html_content)
    if LOG_FULL_DOM:
        try:
            with open(dom_dump_path, "a", encoding="utf-8") as f:
                for node in dom_data:
                    f.write(json.dumps(node, ensure_ascii=False) + "\n")
        except Exception as e:
            logging.error("❌ Failed to write DOM dump: %s", e)

    try:
        logging.debug(
            "📚 DOM summary: %s",
            json.dumps(
                [
                    {"xpath": n["xpath"], "raw_len": len(n["raw"]), "norm_len": len(n["content"])}
                    for n in dom_data
                ],
                ensure_ascii=False,
            ),
        )
    except Exception:
        pass

    # Q&L (optional – kein 400, wenn fehlt)
    qa_config = data.get("questions_and_labels") or {}
    questions = qa_config.get("questions") or []
    labels = qa_config.get("labels") or []

    # LLM nur bei vollständiger Konfig + Q&L
    answers_by_label = {}
    timed_out = False

    have_llm_cfg = all(
        k in params for k in ("ollama_model", "ollama_base", "system_prompt", "llm_timeout_seconds")
    )
    if have_llm_cfg and questions and labels:
        puretext = BeautifulSoup(html_content or "", "html.parser").get_text("\n", strip=True)

        for q, lab in zip(questions, labels, strict=False):
            prompt = f"{params['system_prompt']}\n\nQuestion: {q}\n\nText: {puretext}"

            llm = ask_llm_with_timeout(
                params,
                prompt,
                timeout=int(params["llm_timeout_seconds"]),
                model_name=params["ollama_model"],
            )

            # timeout bookkeeping (nur Flag + optional logfile)
            if llm["status"] == "timeout":
                timed_out = True
                try:
                    with open(timeout_log_path, "a", encoding="utf-8") as f:
                        f.write(f"{task_id}: {lab} :: {q}\n")
                except Exception:
                    pass

            answers_by_label[str(lab)] = {
                "question": q,
                "answer": llm["answer"],  # str|None
                "status": llm["status"],  # ok|timeout|error|model_missing
                "error": llm.get("error"),
            }

    logging.info(
        "🧠 Answers from LLM: %s", json.dumps(answers_by_label, indent=2, ensure_ascii=False)
    )

    dom_match_by_label = {}
    try:
        answers_list = [
            {"label": lab, "question": v.get("question"), "answer": v.get("answer")}
            for lab, v in (answers_by_label or {}).items()
        ]
        prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers_list)

        diag_labels = {
            d.get("label") for d in (diagnostics or []) if isinstance(d, dict) and d.get("label")
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
        logging.warning("extract_xpath_matches_from_dom failed: %s", e)
        prelabels, diagnostics = [], [{"reason": "match_failed", "error": str(e)}]
        dom_match_by_label = {}

    # Audit-Log (best effort)
    try:
        payload_for_log = {
            "task": task_id,
            "model_version": params.get("ollama_model", "stub"),
            "result": prelabels,
        }
        with open(prediction_payload_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload_for_log, indent=2, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.warning("Could not write prediction payload: %s", e)

    meta = {
        "raw_llm_answers": answers_by_label,
        "system_prompt": params.get("system_prompt"),
        "model": params.get("ollama_model"),
        "dom_match_diagnostics": diagnostics,
        "dom_match_by_label": dom_match_by_label,
        "job_id": job_id,
        "performance": perf.to_dict(include_events=False),
    }

    if all(k in params for k in ("label_studio_url", "ls_token")):
        try:
            save_predictions_to_labelstudio(params, task_id, prelabels)  # ohne meta
            attach_meta_to_task(params, int(task_id), meta)
        except Exception as e:
            logging.warning("label studio write failed: %s", e)

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
    return jsonify({"status": "UP"}), 200


# required from label studio for registration
@app.route("/setup", methods=["GET", "POST"])
def setup():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
