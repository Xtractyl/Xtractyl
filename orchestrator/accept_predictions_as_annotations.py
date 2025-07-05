import os
import requests
from dotenv import load_dotenv

load_dotenv()

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
LABEL_STUDIO_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")

HEADERS = {
    "Authorization": f"Token {LABEL_STUDIO_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

log_buffer = []

def get_tasks_with_predictions():
    page = 1
    page_size = 100
    all_tasks = []

    while True:
        url = f"{LABEL_STUDIO_URL}/api/projects/{PROJECT_ID}/tasks?page={page}&page_size={page_size}"
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 404:
                log_buffer.append(f"[INFO] No more pages after page {page}.")
                break
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_buffer.append(f"[ERROR] Failed to fetch page {page}: {e}")
            break

        page_tasks = response.json()
        if not page_tasks:
            break

        all_tasks.extend(page_tasks)
        page += 1

    filtered = [task for task in all_tasks if task.get("predictions")]
    log_buffer.append(f"[INFO] Fetched {len(all_tasks)} total tasks")
    log_buffer.append(f"[INFO] Tasks WITH predictions: {len(filtered)}")
    return filtered

def accept_prediction_as_annotation(task):
    if not task.get("predictions") or task.get("annotations"):
        return False

    prediction = task["predictions"][0]
    result = prediction.get("result")
    if not result:
        return False

    task_id = task["id"]
    payload = {
        "result": result,
        "completed_by": 1,
        "was_cancelled": False,
        "ground_truth": False,
        "lead_time": 0.1,
    }

    url = f"{LABEL_STUDIO_URL}/api/tasks/{task_id}/annotations"
    r = requests.post(url, headers=HEADERS, json=payload)

    content_type = r.headers.get("Content-Type", "")
    if 'application/json' not in content_type:
        log_buffer.append(f"❌ Task {task_id} lieferte HTML statt JSON. Mögliche Ursache: falsche URL oder ungültiger Token.")
        log_buffer.append(f"⚠️ HEADERS: {r.headers}")
        log_buffer.append(f"⚠️ BODY:\n{r.text}")
        return False

    if r.status_code == 201:
        log_buffer.append(f"✅ Prediction für Task {task_id} als Annotation übernommen")
        return True
    else:
        log_buffer.append(f"⚠️ Fehler bei Task {task_id}: {r.status_code} – {r.text}")
        return False

def main():
    tasks = get_tasks_with_predictions()
    accepted = 0
    for task in tasks:
        if accept_prediction_as_annotation(task):
            accepted += 1

    log_buffer.append(f"\n✅ {accepted} Predictions als Annotation übernommen\n")

    # Gib am Ende alle gesammelten Logs aus
    print("\n".join(log_buffer))

if __name__ == "__main__":
    main()