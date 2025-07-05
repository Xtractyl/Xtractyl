import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
LABEL_STUDIO_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
ML_BACKEND_URL = os.getenv("ML_BACKEND_URL", "http://ml-backend:6789")
PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma:latest").replace(":", "_")
HEADERS = {"Authorization": f"Token {LABEL_STUDIO_TOKEN}"}

# Anpassen: persistenter Mount-Ordner mit Modellname im Logfile
SAVE_PATH = f"/app/evaluation/{PROJECT_ID}"
os.makedirs(SAVE_PATH, exist_ok=True)
LOG_FILE = os.path.join(SAVE_PATH, f"{MODEL_NAME}_timing_log.txt")


def get_tasks():
    page = 1
    page_size = 100
    all_tasks = []

    while True:
        url = f"{LABEL_STUDIO_URL}/api/projects/{PROJECT_ID}/tasks?page={page}&page_size={page_size}"
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 404:
                print(f"[INFO] No more pages after page {page}.")
                break
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] Failed to fetch page {page}: {e}")
            break

        page_tasks = response.json()
        if not page_tasks:
            break

        all_tasks.extend(page_tasks)
        page += 1

    filtered = [task for task in all_tasks if not task.get("predictions")]
    print(f"[INFO] Fetched {len(all_tasks)} total tasks")
    print(f"[INFO] Tasks without predictions: {len(filtered)}")
    return filtered


def send_predict(task_id, html):
    payload = {
        "task": {"id": task_id},
        "data": {"html": html}
    }

    url = f"{ML_BACKEND_URL}/predict"
    response = requests.post(url, json=payload)
    print(f"Task {task_id} → Predict: {response.status_code}")
    if response.status_code != 200:
        print("Error:", response.text)


def wait_until_prediction_saved(task_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        url = f"{LABEL_STUDIO_URL}/api/tasks/{task_id}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            task_data = response.json()
            if task_data.get("predictions"):
                print(f"✅ Prediction for Task {task_id} saved.")
                return True
        time.sleep(1)

    print(f"⚠️ Timeout waiting for Task {task_id} prediction.")
    return False


def run_batch():
    tasks = get_tasks()
    print(f"Found {len(tasks)} tasks")

    total_time = 0
    durations = []

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write(f"📋 Timing Log for Project {PROJECT_ID}, Model: {MODEL_NAME}\n")
        log.write(f"Total tasks: {len(tasks)}\n\n")

        for i, task in enumerate(tasks, 1):
            task_id = task["id"]
            html = task["data"].get("html")

            if not html:
                print(f"Task {task_id} has no HTML. Skipping.")
                continue

            start = time.time()
            send_predict(task_id, html)
            wait_until_prediction_saved(task_id)
            duration = time.time() - start
            durations.append(duration)
            total_time += duration

            print(f"⏱️ Task {task_id} finished in {round(duration, 2)} seconds")
            log.write(f"Task {task_id}: {round(duration, 2)} seconds\n")

        if durations:
            avg_time = total_time / len(durations)
            log.write("\n📈 Summary:\n")
            log.write(f"Total processed: {len(durations)} tasks\n")
            log.write(f"Total time: {round(total_time, 2)} seconds\n")
            log.write(f"Average per task: {round(avg_time, 2)} seconds\n")

        print(f"\n📄 Timing log saved to {LOG_FILE}")


if __name__ == "__main__":
    run_batch()