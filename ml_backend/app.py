import json
import logging
import os
import pathlib
import pprint
import re
import unicodedata
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS
from playwright.sync_api import sync_playwright


# ----------------------------------
# Basic logging to console
# ----------------------------------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8080", "http://localhost:5173"]}}, supports_credentials=True)

# ----------------------------------
# Central + per-job logging
# ----------------------------------
LOG_DIR = "/logs"
JOBS_DIR = os.path.join(LOG_DIR, "ml_backend_jobs")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

# General file log
general_logfile = os.path.join(LOG_DIR, "ml_backend.log")
_fh = logging.FileHandler(general_logfile, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger().addHandler(_fh)

def _job_log_paths(job_id: str | None):
    """Return per-job file paths; fall back to general files if job_id is None."""
    if job_id:
        base = os.path.join(JOBS_DIR, job_id)
        os.makedirs(base, exist_ok=True)
        return {
            "payload": os.path.join(base, "prediction_payload.log"),
            "timeouts": os.path.join(base, "timeout_tasks.log"),
        }
    else:
        return {
            "payload": os.path.join(LOG_DIR, "prediction_payload.log"),
            "timeouts": os.path.join(LOG_DIR, "timeout_tasks.log"),
        }

# ----------------------------------
# Utilities
# ----------------------------------
def normalize_text(text):
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize("NFKC", text).replace("\n", "").strip()

def get_offset_in_original(original_text, normalized_target, start_in_normalized):
    norm = ""
    orig_index = 0
    match_start, match_end = None, None
    while orig_index < len(original_text):
        c = original_text[orig_index]
        norm_c = unicodedata.normalize("NFKC", c)
        norm += norm_c
        if match_start is None and len(norm) > start_in_normalized:
            match_start = orig_index
        if len(norm) >= start_in_normalized + len(normalized_target):
            match_end = orig_index + 1
            break
        orig_index += 1
    if match_start is not None and match_end is not None:
        candidate = original_text[match_start:match_end]
        if normalize_text(candidate) == normalized_target:
            return match_start, match_end
    return None, None

def clean_xpath(raw_xpath):
    raw_xpath = re.sub(r"^/html(\[1\])?/body(\[1\])?", "", raw_xpath)
    raw_xpath = re.sub(r"/text\(\)\[1\]$", "", raw_xpath)
    if not raw_xpath.startswith("/"):
        raw_xpath = "/" + raw_xpath
    return raw_xpath

def extract_xpath_matches_from_dom(dom_data, answers):
    matches, diagnostics = [], []
    dom_data_sorted = sorted(dom_data, key=lambda el: len(el.get("content", "")))
    for ans in answers:
        if not ans["answer"] or ans["answer"] in ("<no answer>", "<keine Antwort>"):
            continue
        normalized_answer = normalize_text(ans["answer"])
        found_match = False
        for el in dom_data_sorted:
            content = el.get("content", "")
            xpath = el.get("xpath", "")
            if not content or not xpath:
                continue
            normalized_content = normalize_text(content)
            offset_norm = normalized_content.find(normalized_answer)
            if offset_norm == -1:
                continue
            start_offset, end_offset = get_offset_in_original(content, normalized_answer, offset_norm)
            if start_offset is None:
                diagnostics.append({"label": ans["label"], "xpath": xpath, "reason": "Offset mapping failed"})
                continue
            matches.append({
                "id": str(uuid.uuid4()),
                "from_name": "label",
                "to_name": "html",
                "type": "labels",
                "origin": "prediction",
                "value": {
                    "start": xpath,
                    "end": xpath,
                    "startOffset": start_offset,
                    "endOffset": end_offset,
                    "labels": [ans["label"]],
                    "text": ans["answer"],
                },
            })
            found_match = True
            break
        if not found_match:
            diagnostics.append({"label": ans["label"], "reason": "Not found in any content block"})
    return matches, diagnostics

def save_predictions_to_labelstudio(params, task_id, prediction_result):
    url = params["label_studio_url"]
    token = params["ls_token"]
    mv = params["ollama_model"]
    logging.info(f"📤 Saving predictions for task {task_id} (model: {mv})")

    payload = {"task": task_id, "model_version": mv, "result": prediction_result}

    try:
        response = requests.post(
            f"{url}/api/predictions",
            headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        logging.info(f"✅ Prediction stored in Label Studio (task {task_id})")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"❌ HTTP Error: {http_err} - {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"❌ Error sending to Label Studio: {e}")

def ensure_model_available(params, model_name: str):
    base = params["ollama_base"]
    try:
        r = requests.get(f"{base}/api/tags", timeout=10)
        r.raise_for_status()
        local_models = [m.get("name") or m.get("model") for m in r.json().get("models", [])]
        local_models = [m for m in local_models if m]
        if model_name in local_models:
            return True

        logging.info(f"📦 Model '{model_name}' not present — pulling…")
        pull = requests.post(f"{base}/api/pull", json={"name": model_name}, stream=True, timeout=600)
        for line in pull.iter_lines():
            if line:
                logging.debug("📥 %s", line.decode("utf-8"))
        logging.info(f"✅ Model '{model_name}' pulled.")
        return True
    except Exception as e:
        logging.error(f"❌ Error ensuring model '{model_name}': {e}")
        return False

def ask_llm_with_timeout(params, prompt: str, timeout: int, model_name: str):
    base = params["ollama_base"]
    if not ensure_model_available(params, model_name):
        return "<no answer>"
    try:
        response = requests.post(
            f"{base}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        logging.error(f"❌ Timeout or error while calling LLM: {e}")
        return "<no answer>"

def extract_dom_with_chromium(html: str):
    extracted = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        elements = page.query_selector_all("body *")
        for el in elements:
            try:
                text = el.inner_text().strip()
                if not text:
                    continue
                xpath = page.evaluate(
                    """el => {
                        function getXPath(e) {
                            if (e.id) return '//*[@id="' + e.id + '"]';
                            if (e === document.body) return '/html/body';
                            let ix = 1;
                            const siblings = e.parentNode ? e.parentNode.childNodes : [];
                            for (let i = 0; i < siblings.length; i++) {
                                const s = siblings[i];
                                if (s === e) return getXPath(e.parentNode) + '/' + e.tagName.toLowerCase() + '[' + ix + ']';
                                if (s.nodeType === 1 && s.tagName === e.tagName) ix++;
                            }
                            return '';
                        }
                        return getXPath(el);
                    }""",
                    el,
                )
                cleaned_xpath = clean_xpath(xpath)
                extracted.append({"xpath": cleaned_xpath, "content": text})
            except Exception:
                continue
        browser.close()
    return extracted

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json() or {}
    # Extract config entirely from payload
    params = data.get("config", {})
    required = ["label_studio_url", "ls_token", "ollama_model", "ollama_base", "system_prompt", "llm_timeout_seconds"]
    missing = [r for r in required if r not in params]
    if missing:
        return jsonify({"error": f"Missing config parameters: {', '.join(missing)}"}), 400

    job_id = request.headers.get("X-Prelabel-Job") or request.args.get("job_id") or data.get("job_id")
    job_paths = _job_log_paths(job_id)
    prediction_payload_path = job_paths["payload"]
    timeout_log_path = pathlib.Path(job_paths["timeouts"])

    # select task object
    task_obj = data.get("task") or (data.get("tasks") or [{}])[0]
    task_id = task_obj.get("id") or task_obj.get("pk") or task_obj.get("task_id") or data.get("task_id") or data.get("id")
    if not task_id:
        return jsonify({"error": "task id missing"}), 400

    # get HTML content
    html_content = ""
    d = (task_obj.get("data") or data.get("data") or {})
    for k in ("html", "text", "content", "raw"):  # try common keys
        if isinstance(d.get(k), str) and d[k].strip():
            html_content = d[k]
            break
    if not html_content and isinstance(data.get("html"), str):
        html_content = data.get("html")
    if not html_content:
        return jsonify({"error": "HTML content missing"}), 400

    # Extract and predict
    dom_data = extract_dom_with_chromium(html_content)

    # Load QA config from request
    qa_config = data.get("questions_and_labels") or {}
    questions = qa_config.get("questions", [])
    labels = qa_config.get("labels", [])
    
    if not questions or not labels:
        return jsonify({"error": "questions_and_labels must include both 'questions' and 'labels'."}), 400
    questions, labels = qa_config.get("questions", []), qa_config.get("labels", [])
    puretext = BeautifulSoup(html_content, "html.parser").get_text("\n", strip=True)

    answers, timed_out = [], False
    for q, lab in zip(questions, labels):
        prompt = f"{params['system_prompt']}\n\nQuestion: {q}\n\nText: {puretext}"
        output = ask_llm_with_timeout(params, prompt, timeout=int(params['llm_timeout_seconds']), model_name=params['ollama_model'])
        if output == "<no answer>":
            timed_out = True
            with open(timeout_log_path, "a", encoding="utf-8") as f:
                f.write(f"{task_id}: {q}\n")
        answers.append({"question": q, "label": lab, "answer": None if output == "<no answer>" else output})
    logging.info(f"🧠 Answers from LLM: {json.dumps(answers, indent=2, ensure_ascii=False)}")
    prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers)

    # Log payload
    payload_for_log = {"task": task_id, "model_version": params['ollama_model'], "result": prelabels}
    with open(prediction_payload_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload_for_log, indent=2, ensure_ascii=False) + "\n")

    # Send to Label Studio
    save_predictions_to_labelstudio(params, task_id, prelabels)

    return jsonify({
        "results": [{"model_version": params['ollama_model'], "score": 1.0, "result": prelabels}],
        "meta": {"answers": answers, "diagnostics": diagnostics, "status": "timeout" if timed_out else "success", "task_id": task_id, "job_id": job_id}
    }), 200
    
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6789, debug=True)