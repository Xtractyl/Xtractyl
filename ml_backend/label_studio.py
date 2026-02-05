# /ml_backend/label_studio.py
import requests


def save_predictions_to_labelstudio(params, task_id, prediction_result, meta: dict | None = None):
    url = params["label_studio_url"]
    token = params["ls_token"]
    mv = params["ollama_model"]

    payload = {"task": task_id, "model_version": mv, "result": prediction_result}
    if meta:
        payload["meta"] = meta

    try:
        response = requests.post(
            f"{url}/api/predictions",
            headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        pass


def attach_meta_to_task(params, task_id: int, meta: dict):
    url = params["label_studio_url"]
    token = params["ls_token"]

    r = requests.get(
        f"{url}/api/tasks/{task_id}",
        headers={"Authorization": f"Token {token}"},
        timeout=15,
    )
    r.raise_for_status()
    task = r.json()
    data = task.get("data") or {}

    data["ml_meta"] = meta

    pr = requests.patch(
        f"{url}/api/tasks/{task_id}",
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        json={"data": data},
        timeout=15,
    )
    pr.raise_for_status()
