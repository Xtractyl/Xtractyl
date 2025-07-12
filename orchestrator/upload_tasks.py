import os

import requests
from dotenv import load_dotenv

load_dotenv()  # Lädt Umgebungsvariablen aus .env-Datei
LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
API_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")  # konsistent mit create_project.py
PROJECT_ID = int(os.getenv("LABEL_STUDIO_PROJECT_ID"))
HTML_FOLDER = "data/htmls"
BATCH_SIZE = 50


HEADERS = {"Authorization": f"Token {API_TOKEN}", "Content-Type": "application/json"}


def collect_html_tasks(folder):
    tasks = []
    for filename in os.listdir(folder):
        if filename.endswith(".html"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
                tasks.append({"data": {"html": html_content}})
    return tasks


def upload_in_batches(tasks, batch_size):
    url = f"{LABEL_STUDIO_URL}/api/projects/{PROJECT_ID}/import"
    total = len(tasks)
    for i in range(0, total, batch_size):
        batch = tasks[i : i + batch_size]
        try:
            response = requests.post(url, headers=HEADERS, json=batch)
            print(f"📤 Batch {i // batch_size + 1}: Status {response.status_code}")
            if response.status_code != 201:
                print("❌ Fehler beim Import:")
                print(response.text)
                break
        except Exception as e:
            print("🚨 Upload-Fehler:", str(e))
            break


if __name__ == "__main__":
    print("Token und Project ID:")
    print(API_TOKEN, PROJECT_ID)
    print(f"🔍 Suche HTML-Dateien in {HTML_FOLDER} ...")
    tasks = collect_html_tasks(HTML_FOLDER)
    print(f"📦 {len(tasks)} HTML-Dateien gefunden.")
    if tasks:
        upload_in_batches(tasks, BATCH_SIZE)
    else:
        print("⚠️ Keine HTML-Dateien gefunden.")
