import json
import logging
import os
import pathlib
import re
import unicodedata
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS
from playwright.sync_api import sync_playwright

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

def origin_from_env(prefix: str, default_port: int, default_host: str = "localhost") -> str:
    origin = os.getenv(f"{prefix}_ORIGIN") or os.getenv(f"{prefix}_URL")
    if origin:
        return origin
    host = os.getenv(f"{prefix}_HOST", default_host)
    port = os.getenv(f"{prefix}_PORT", str(default_port))
    scheme = os.getenv(f"{prefix}_SCHEME", "http")
    return f"{scheme}://{host}:{port}"

FRONTEND_ORIGIN = origin_from_env("FRONTEND_PORT", 5173)
LABELSTUDIO_ORIGIN = origin_from_env("LABELSTUDIO_PORT", 8080)

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
            "dom_dump": os.path.join(base, "dom_dump.jsonl"),
        }
    else:
        return {
            "payload": os.path.join(LOG_DIR, "prediction_payload.log"),
            "timeouts": os.path.join(LOG_DIR, "timeout_tasks.log"),
            "dom_dump": os.path.join(LOG_DIR, "dom_dump.jsonl"),
        }

# ----------------------------------
# Normalization helpers
# ----------------------------------
def _norm_char(c: str) -> str:
    # char-wise normalization without strip so lengths map correctly
    return (
        unicodedata.normalize("NFKC", c)
        .replace("\u00AD", "")    # soft hyphen
        .replace("\u00A0", " ")   # NBSP -> space
        .replace("\r", "")
        .replace("\n", "")
    )

def build_norm_index(original_text: str):
    """
    Returns (norm_text, index_map)
    index_map[j] = original index for the j-th character in norm_text.
    """
    norm_parts = []
    index_map = []
    for i, ch in enumerate(original_text):
        n = _norm_char(ch)
        if not n:
            continue
        norm_parts.append(n)
        for _ in range(len(n)):
            index_map.append(i)
    return "".join(norm_parts), index_map

def normalize_text_block(text: str) -> str:
    # block normalization used for answers (trim OK)
    return (
        unicodedata.normalize("NFKC", text or "")
        .replace("\u00AD", "")
        .replace("\u00A0", " ")
        .replace("\r", "")
        .replace("\n", "")
        .strip()
    )

def clean_xpath(raw_xpath: str) -> str:
    raw_xpath = re.sub(r"^/html(\[1\])?/body(\[1\])?", "", raw_xpath)
    raw_xpath = re.sub(r"/text\(\)\[1\]$", "", raw_xpath)
    if not raw_xpath.startswith("/"):
        raw_xpath = "/" + raw_xpath
    return raw_xpath

# ----------------------------------
# DOM extraction (raw + normalized + index_map)
# ----------------------------------
def extract_dom_with_chromium(html: str):
    """
    Returns list of dicts:
      {
        "xpath": str,
        "raw": original textContent,
        "content": normalized text,
        "index_map": list[int] mapping normalized indices -> original indices
      }
    """
    extracted = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")

        elements = page.query_selector_all("body *")
        for el in elements:
            try:
                raw_text = page.evaluate("el => el.textContent", el) or ""
                norm_text, index_map = build_norm_index(raw_text)
                if not norm_text:
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
                extracted.append({
                    "xpath": cleaned_xpath,
                    "raw": raw_text,
                    "content": norm_text,
                    "index_map": index_map,
                })
            except Exception:
                continue

        browser.close()
    return extracted

# ----------------------------------
# Matching
# ----------------------------------
def extract_xpath_matches_from_dom(dom_data, answers):
    """
    dom_data: list of {"xpath", "raw", "content", "index_map"}
    answers:  list of {"question", "label", "answer"}
    """
    matches, diagnostics = [], []

    logging.debug("🔎 Starting DOM matching: %d DOM blocks, %d answers", len(dom_data), len(answers))

    # sort by normalized content length asc (tighter nodes first)
    dom_sorted = sorted(dom_data, key=lambda el: len(el.get("content") or ""))

    for idx, ans in enumerate(answers, start=1):
        if not ans["answer"] or ans["answer"] in ("<no answer>", "<keine Antwort>"):
            continue

        normalized_answer = normalize_text_block(ans["answer"])
        logging.debug(
            "🧩 [%d] Label=%s | normalized_answer=%r (len=%d)",
            idx, ans["label"], normalized_answer, len(normalized_answer)
        )

        found_match = False
        for el in dom_sorted:
            content = el.get("content") or ""
            xpath = el.get("xpath") or ""
            if not content or not xpath:
                continue

            offset_norm = content.find(normalized_answer)
            if offset_norm == -1:
                continue

            index_map = el.get("index_map") or []
            if not index_map or offset_norm + len(normalized_answer) - 1 >= len(index_map):
                diagnostics.append({
                    "label": ans["label"],
                    "xpath": xpath,
                    "reason": "Index map missing/short"
                })
                logging.debug(
                    "❌ [%d] Index map missing/short | xpath=%s | offset_norm=%d | ans_len=%d | map_len=%d",
                    idx, xpath, offset_norm, len(normalized_answer), len(index_map)
                )
                continue

            start_orig = index_map[offset_norm]
            end_orig = index_map[offset_norm + len(normalized_answer) - 1] + 1  # slice end exclusive

            if start_orig is None or end_orig is None or start_orig < 0 or end_orig <= start_orig:
                diagnostics.append({"label": ans["label"], "xpath": xpath, "reason": "Offset mapping failed"})
                logging.debug(
                    "❌ [%d] Offset mapping failed | xpath=%s | offset_norm=%d | start_orig=%s | end_orig=%s",
                    idx, xpath, offset_norm, start_orig, end_orig
                )
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
                    "startOffset": start_orig,
                    "endOffset": end_orig,
                    "labels": [ans["label"]],
                    "text": ans["answer"],
                },
            })
            logging.debug(
                "✅ [%d] Match | xpath=%s | start_orig=%d | end_orig=%d | norm_offset=%d",
                idx, xpath, start_orig, end_orig, offset_norm
            )
            found_match = True
            break

        if not found_match:
            diagnostics.append({"label": ans["label"], "reason": "Not found in any content block"})
            logging.debug("🔍 [%d] No match for label=%s | normalized_answer=%r", idx, ans["label"], normalized_answer)

    logging.info("🧾 Match summary: %d matches, %d diagnostics", len(matches), len(diagnostics))
    if diagnostics:
        logging.debug("🧪 Diagnostics: %s", json.dumps(diagnostics, ensure_ascii=False))
    return matches, diagnostics

# ----------------------------------
# LS, model, LLM
# ----------------------------------
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

# ----------------------------------
# Routes
# ----------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json() or {}
    params = data.get("config", {})
    required = ["label_studio_url", "ls_token", "ollama_model", "ollama_base", "system_prompt", "llm_timeout_seconds"]
    missing = [r for r in required if r not in params]
    if missing:
        return jsonify({"error": f"Missing config parameters: {', '.join(missing)}"}), 400

    job_id = request.headers.get("X-Prelabel-Job") or request.args.get("job_id") or data.get("job_id")
    job_paths = _job_log_paths(job_id)
    prediction_payload_path = job_paths["payload"]
    timeout_log_path = pathlib.Path(job_paths["timeouts"])
    dom_dump_path = pathlib.Path(job_paths["dom_dump"])

    # task object
    task_obj = data.get("task") or (data.get("tasks") or [{}])[0]
    task_id = task_obj.get("id") or task_obj.get("pk") or task_obj.get("task_id") or data.get("task_id") or data.get("id")
    if not task_id:
        return jsonify({"error": "task id missing"}), 400

    # HTML
    html_content = ""
    d = (task_obj.get("data") or data.get("data") or {})
    for k in ("html", "text", "content", "raw"):
        if isinstance(d.get(k), str) and d[k].strip():
            html_content = d[k]
            break
    if not html_content and isinstance(data.get("html"), str):
        html_content = data.get("html")
    if not html_content:
        return jsonify({"error": "HTML content missing"}), 400

    # Extract DOM
    dom_data = extract_dom_with_chromium(html_content)

    # Full DOM dump (toggle)
    if LOG_FULL_DOM:
        try:
            with open(dom_dump_path, "a", encoding="utf-8") as f:
                for node in dom_data:
                    f.write(json.dumps(node, ensure_ascii=False) + "\n")
            logging.info("🗂️ Full DOM dumped to %s (%d nodes)", str(dom_dump_path), len(dom_data))
        except Exception as e:
            logging.error("❌ Failed to write DOM dump: %s", e)

    # Always write compact DOM summary to main log
    try:
        logging.debug(
            "📚 DOM summary: %s",
            json.dumps(
                [{"xpath": n["xpath"], "raw_len": len(n["raw"]), "norm_len": len(n["content"])} for n in dom_data],
                ensure_ascii=False,
            ),
        )
    except Exception:
        pass

    # Q&L
    qa_config = data.get("questions_and_labels") or {}
    questions = qa_config.get("questions", [])
    labels = qa_config.get("labels", [])
    if not questions or not labels:
        return jsonify({"error": "questions_and_labels must include both 'questions' and 'labels'."}), 400

    # Plain text for LLM
    puretext = BeautifulSoup(html_content, "html.parser").get_text("\n", strip=True)

    # LLM answers
    answers, timed_out = [], False
    for q, lab in zip(questions, labels):
        prompt = f"{params['system_prompt']}\n\nQuestion: {q}\n\nText: {puretext}"
        output = ask_llm_with_timeout(
            params,
            prompt,
            timeout=int(params["llm_timeout_seconds"]),
            model_name=params["ollama_model"],
        )
        if output == "<no answer>":
            timed_out = True
            try:
                with open(timeout_log_path, "a", encoding="utf-8") as f:
                    f.write(f"{task_id}: {q}\n")
            except Exception:
                pass
        answers.append({"question": q, "label": lab, "answer": None if output == "<no answer>" else output})

    logging.info("🧠 Answers from LLM: %s", json.dumps(answers, indent=2, ensure_ascii=False))

    # Match
    prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers)

    # Log payload
    payload_for_log = {"task": task_id, "model_version": params["ollama_model"], "result": prelabels}
    with open(prediction_payload_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload_for_log, indent=2, ensure_ascii=False) + "\n")

    # Send to Label Studio
    save_predictions_to_labelstudio(params, task_id, prelabels)

    return jsonify({
        "results": [{"model_version": params["ollama_model"], "score": 1.0, "result": prelabels}],
        "meta": {
            "answers": answers,
            "diagnostics": diagnostics,
            "status": "timeout" if timed_out else "success",
            "task_id": task_id,
            "job_id": job_id
        }
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP"}), 200

# required from label studio for registration
@app.route("/setup", methods=["GET", "POST"])
def setup():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)