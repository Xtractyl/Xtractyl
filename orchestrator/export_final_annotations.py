import os
import csv
import requests
import hashlib
from dotenv import load_dotenv

load_dotenv()

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
LABEL_STUDIO_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")

HEADERS = {"Authorization": f"Token {LABEL_STUDIO_TOKEN}"}

SAVE_DIR = f"/app/evaluation/{PROJECT_ID}"
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_PATH = os.path.join(SAVE_DIR, "final_annotations.csv")


def fetch_tasks(project_id):
    page = 1
    all_tasks = []
    while True:
        url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks?page={page}&page_size=100"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 404:
            break
        r.raise_for_status()
        tasks = r.json()
        if not tasks:
            break
        all_tasks.extend(tasks)
        page += 1
    return [t for t in all_tasks if t.get("annotations")]


def get_html_hash(task):
    html = task.get("data", {}).get("html", "")
    return hashlib.md5(html.encode("utf-8")).hexdigest() if html else None


def extract_labels(annotation_result):
    return {
        res["value"]["labels"][0]: res["value"]["text"]
        for res in annotation_result
        if "labels" in res["value"] and "text" in res["value"]
    }


def main():
    print(f"📥 Lade finale Annotationen aus Projekt {PROJECT_ID}")
    tasks = fetch_tasks(PROJECT_ID)
    print(f"✅ {len(tasks)} Tasks mit Annotationen gefunden")

    all_rows = []
    all_labels = set()

    for task in tasks:
        result = task["annotations"][0].get("result", [])
        label_data = extract_labels(result)
        all_labels.update(label_data.keys())

        row = {
            "task_id": task["id"],
            "html_hash": get_html_hash(task),
        }
        row.update({label: label_data.get(label, "") for label in all_labels})
        all_rows.append(row)

    sorted_labels = sorted(all_labels)
    fieldnames = ["task_id", "html_hash"] + sorted_labels

    with open(SAVE_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ Finale Annotationen gespeichert unter: {SAVE_PATH}")


if __name__ == "__main__":
    main()