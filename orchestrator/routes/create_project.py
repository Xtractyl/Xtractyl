import json
import os
import requests
from datetime import datetime

LOGFILE_PATH = "/logs/orchestrator.log"

def log_to_file(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def create_project_main_from_payload(payload):
    logs = []

    # Eingaben aus dem Payload
    title = payload.get("title", "xtractyl_project")
    questions = payload.get("questions", [])
    labels = payload.get("labels", [])
    token = payload.get("token", None)

    log_to_file(f"📥 Projektanlage gestartet für: '{title}'")
    log_to_file(f"→ Fragen: {questions}")
    log_to_file(f"→ Labels: {labels}")

    if not all([title, questions, labels, token]):
        log_to_file("❌ Fehlende Eingaben im Payload.")
        raise ValueError("❌ Titel, Fragen, Labels und Token sind erforderlich.")

    # Projektordner anlegen
    base_path = os.path.join("data", "projects", title)
    os.makedirs(base_path, exist_ok=True)
    log_to_file(f"📁 Projektordner erstellt (falls nicht vorhanden): {base_path}")

    # Speichere questions_and_labels.json
    qa = {"questions": questions, "labels": labels}
    qa_path = os.path.join(base_path, "questions_and_labels.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    msg = f"✅ questions_and_labels.json gespeichert unter: {qa_path}"
    logs.append(msg)
    log_to_file(msg)

    # Label-Studio API-Konfiguration
    LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
    LABEL_CONFIG_TEMPLATE = """
    <View>
        <View style="padding: 0 1em; margin: 1em 0; background: #f1f1f1; position: sticky; top: 0; border-radius: 3px; z-index:100">
          <Labels name="label" toName="html">
            {labels}
          </Labels>
        </View>
        <HyperText name="html" value="$html" granularity="symbol" />
    </View>
    """
    label_tags = "\n    ".join([f'<Label value="{label}"/>' for label in labels])
    label_config = LABEL_CONFIG_TEMPLATE.format(labels=label_tags)

    # Projekt anlegen
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {"title": title, "label_config": label_config}

    try:
        response = requests.post(f"{LABEL_STUDIO_URL}/api/projects", headers=headers, json=payload)
    except Exception as e:
        log_to_file(f"❌ Netzwerkfehler beim Projektanlegen: {e}")
        raise

    if response.status_code != 201:
        error_msg = f"❌ Fehler beim Erstellen des Projekts: {response.text}"
        logs.append(error_msg)
        log_to_file(error_msg)
        raise RuntimeError(error_msg)

    project_id = response.json()["id"]
    msg = f"✅ Projekt '{title}' erstellt mit ID {project_id}"
    logs.append(msg)
    log_to_file(msg)

    # ML Backend verknüpfen
    ml_backend_url = os.getenv("ML_BACKEND_URL", "http://ml_backend:6789")
    ml_payload = {"url": ml_backend_url, "title": "xtractyl-backend", "project": project_id}

    try:
        ml_response = requests.post(f"{LABEL_STUDIO_URL}/api/ml", headers=headers, json=ml_payload)
    except Exception as e:
        log_to_file(f"⚠️ Netzwerkfehler beim Zuweisen des ML-Backends: {e}")
        raise

    if ml_response.status_code != 201:
        msg = f"⚠️ ML Backend konnte nicht verbunden werden: {ml_response.text}"
        logs.append(msg)
        log_to_file(msg)
    else:
        msg = "✅ ML Backend erfolgreich zugewiesen."
        logs.append(msg)
        log_to_file(msg)

    return logs