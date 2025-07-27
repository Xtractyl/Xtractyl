import os
import requests
from flask import request, jsonify

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
BATCH_SIZE = 50

def collect_html_tasks(folder):
    tasks = []
    for filename in os.listdir(folder):
        if filename.endswith(".html"):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
                tasks.append({"data": {"html": html}})
    return tasks

def upload_in_batches(tasks, batch_size, logs, project_id, headers):
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks/bulk"
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        try:
            resp = requests.post(url, headers=headers, json=batch)
            logs.append(f"📦 Batch {i // batch_size + 1}: {resp.status_code}")
            if resp.status_code != 201:
                logs.append("❌ Fehler beim Upload:")
                logs.append(resp.text)
                break
        except Exception as e:
            logs.append(f"❌ Upload-Fehler: {e}")
            break

def upload_tasks_main_from_payload(payload):
    title = payload.get("project_name")
    token = payload.get("token")
    html_folder_name = payload.get("html_folder")

    if not title or not token or not html_folder_name:
        raise ValueError("❌ project_name, token und html_folder erforderlich.")

    html_folder = os.path.join("data", "htmls", html_folder_name)
    if not os.path.isdir(html_folder):
        raise FileNotFoundError(f"❌ Ordner nicht gefunden: {html_folder}")
    
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    r = requests.get(f"{LABEL_STUDIO_URL}/api/projects", headers=headers)
    if r.status_code != 200:
        raise RuntimeError("❌ Konnte Projekte nicht laden.")
    
    projects = r.json() if isinstance(r.json(), list) else r.json().get("projects") or r.json().get("results") or []
    project_id = next((p["id"] for p in projects if p["title"] == title), None)

    if not project_id:
        raise ValueError(f"❌ Projekt '{title}' nicht gefunden.")

    logs = [f"🔍 HTMLs in {html_folder} ..."]
    tasks = collect_html_tasks(html_folder)
    logs.append(f"📄 {len(tasks)} HTML-Dateien gefunden.")

    if tasks:
        upload_in_batches(tasks, BATCH_SIZE, logs, project_id, headers)
    else:
        logs.append("⚠️ Keine HTML-Dateien gefunden.")

    # optional: persist log
    os.makedirs("logs", exist_ok=True)
    with open("logs/orchestrator.log", "a", encoding="utf-8") as f:
        f.write("\n".join(logs) + "\n")

    return logs