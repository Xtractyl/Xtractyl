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
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": ["http://localhost:8080"]}},
    supports_credentials=True,
)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:latest")
LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL")
LS_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 1200))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "System prompt not defined.")

timeout_log_path = pathlib.Path("./timeout_tasks.log")


# --------------------- UTILITIES ---------------------


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
        if not ans["answer"] or ans["answer"] == "<keine Antwort>":
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
            start_offset, end_offset = get_offset_in_original(
                content, normalized_answer, offset_norm
            )
            if start_offset is None:
                diagnostics.append(
                    {
                        "label": ans["label"],
                        "xpath": xpath,
                        "reason": "Offset mapping failed",
                    }
                )
                continue
            matches.append(
                {
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
                }
            )
            found_match = True
            break
        if not found_match:
            diagnostics.append(
                {"label": ans["label"], "reason": "Not found in any content block"}
            )
    return matches, diagnostics


def save_predictions_to_labelstudio(task_id, prediction_result):
    logging.info(
        f"📤 Sende Predictions für Task {task_id} an Label Studio mit Modell: {OLLAMA_MODEL}"
    )

    payload = {
        "task": task_id,
        "model_version": OLLAMA_MODEL,
        "result": prediction_result,
    }

    try:
        response = requests.post(
            f"{LABEL_STUDIO_URL}/api/predictions",
            headers={
                "Authorization": f"Token {LS_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        logging.info(
            f"✅ Prediction erfolgreich in Label Studio gespeichert (Task {task_id})"
        )
    except requests.exceptions.HTTPError as http_err:
        logging.error(
            f"❌ HTTP Error: {http_err} - {response.status_code} {response.text}"
        )
    except Exception as e:
        logging.error(f"❌ Fehler beim Senden an Label Studio: {e}")

    with open("prediction_payload.log", "a", encoding="utf-8") as f:
        f.write(f"\n📤 Task {task_id} Prediction Payload:\n")
        f.write(json.dumps(payload, indent=2, ensure_ascii=False))
        f.write("\n" + "=" * 80 + "\n")


def ensure_model_available(model_name):
    try:
        response = requests.get("http://ollama:11434/api/tags", timeout=10)
        response.raise_for_status()
        local_models = [m["name"] for m in response.json().get("models", [])]
        if model_name in local_models:
            return True

        logging.info(
            f"📦 Modell '{model_name}' nicht lokal gefunden – starte Download..."
        )
        pull = requests.post(
            "http://ollama:11434/api/pull", json={"name": model_name}, stream=True
        )
        for line in pull.iter_lines():
            if line:
                logging.debug(f"📥 {line.decode('utf-8')}")
        logging.info(f"✅ Modell '{model_name}' wurde erfolgreich geladen.")
        return True
    except Exception as e:
        logging.error(f"❌ Fehler beim Download des Modells '{model_name}': {e}")
        return False


def ask_llm_with_timeout(prompt, timeout):
    if not ensure_model_available(OLLAMA_MODEL):
        return "<Modell nicht verfügbar>"
    try:
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        logging.error(f"❌ Timeout or error while calling LLM: {e}")
        return "<keine Antwort>"


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


# --------------------- ENDPOINTS ---------------------


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    task = data.get("task")
    task_id = task.get("id")
    html_content = data.get("data", {}).get("html", "")

    if not html_content:
        return jsonify({"error": "HTML content missing"}), 400

    dom_data = extract_dom_with_chromium(html_content)
    logging.debug(f"🌐 DOM für Task {task_id}:\n{pprint.pformat(dom_data, width=120)}")

    with open("questions_and_labels.json", "r", encoding="utf-8") as f:
        qa_config = json.load(f)

    questions, labels = qa_config["questions"], qa_config["labels"]
    puretext = BeautifulSoup(html_content, "html.parser").get_text("\n", strip=True)

    answers = []
    timed_out = False

    # ✅ Frühzeitiger Modellcheck
    if not ensure_model_available(OLLAMA_MODEL):
        for question, label in zip(questions, labels):
            answers.append({"question": question, "label": label, "answer": None})

        return jsonify(
            {
                "results": [],
                "meta": {
                    "answers": answers,
                    "diagnostics": [],
                    "status": "model_unavailable",
                    "task_id": task_id,
                },
            }
        )

    for question, label in zip(questions, labels):
        prompt = f"""{SYSTEM_PROMPT}

Frage: {question}

Text: {puretext}
"""
        logging.info(f"🧠 Frage: {question}")
        output = ask_llm_with_timeout(prompt, timeout=LLM_TIMEOUT_SECONDS)
        logging.info(f"📝 LLM-Antwort: {output}")

        if output == "<keine Antwort>":
            timed_out = True
            with open(timeout_log_path, "a", encoding="utf-8") as f:
                f.write(f"{task_id}: {question}\n")

        parsed = None if output == "<keine Antwort>" else output
        answers.append({"question": question, "label": label, "answer": parsed})

    prelabels, diagnostics = extract_xpath_matches_from_dom(dom_data, answers)

    try:
        save_predictions_to_labelstudio(task_id, prelabels)
    except Exception as e:
        logging.error(f"❌ Fehler beim Speichern in Label Studio: {e}")

    return jsonify(
        {
            "results": [
                {"model_version": OLLAMA_MODEL, "score": 1.0, "result": prelabels}
            ],
            "meta": {
                "answers": answers,
                "diagnostics": diagnostics,
                "status": "timeout" if timed_out else "success",
                "task_id": task_id,
            },
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP"})


@app.route("/setup", methods=["POST"])
def setup():
    config = request.json
    logging.info(f"Received setup config: {config}")
    return jsonify({"status": "setup completed"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6789, debug=True)
