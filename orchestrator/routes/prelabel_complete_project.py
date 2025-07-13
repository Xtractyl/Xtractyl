import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
LABEL_STUDIO_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
ML_BACKEND_URL = os.getenv("ML_BACKEND_URL", "http://ml-backend:6789")
PROJECT_ID = os.getenv("LABEL_STUDIO_PROJECT_ID")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma:latest").replace(":", "_")
HEADERS = {"Authorization": f"Token {LABEL_STUDIO_TOKEN}"}

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
                break
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            break

        page_tasks = response.json()
        if not page_tasks:
            break

        all_tasks.extend(page_tasks)
        page += 1

    return [task for task in all_tasks if not task.get("predictions")]


def send_predict(task_id, html):
    payload = {"task": {"id": task_id}, "data": {"html": html}}
    url = f"{ML_BACKEND_URL}/predict"
    return requests.post(url, json=payload)


def wait_until_prediction_saved(task_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        url = f"{LABEL_STUDIO_URL}/api/tasks/{task_id}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200 and response.json().get("predictions"):
            return True
        time.sleep(1)
    return False


def prelabel_complete_project_main():
    logs = []
    tasks = get_tasks()
    logs.append(f"[INFO] Found {len(tasks)} tasks without predictions.")

    total_time = 0
    durations = []

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write(f"📋 Timing Log for Project {PROJECT_ID}, Model: {MODEL_NAME}\n")
        log.write(f"Total tasks: {len(tasks)}\n\n")

        for task in tasks:
            task_id = task["id"]
            html = task["data"].get("html")

            if not html:
                logs.append(f"[WARN] Task {task_id} has no HTML. Skipping.")
                continue

            start = time.time()
            response = send_predict(task_id, html)
            logs.append(f"[SEND] Task {task_id} → Predict: {response.status_code}")

            success = wait_until_prediction_saved(task_id)
            duration = time.time() - start
            durations.append(duration)
            total_time += duration

            logs.append(f"[TIME] Task {task_id} finished in {round(duration, 2)} seconds")
            log.write(f"Task {task_id}: {round(duration, 2)} seconds\n")

        if durations:
            avg_time = total_time / len(durations)
            log.write("\n📈 Summary:\n")
            log.write(f"Total processed: {len(durations)} tasks\n")
            log.write(f"Total time: {round(total_time, 2)} seconds\n")
            log.write(f"Average per task: {round(avg_time, 2)} seconds\n")

    logs.append(f"📄 Timing log saved to {LOG_FILE}")
    return logs


def prelabel_complete_project_main_wrapper():
    return prelabel_complete_project_main()

if __name__ == "__main__":
    for line in prelabel_complete_project_main():
        print(line)