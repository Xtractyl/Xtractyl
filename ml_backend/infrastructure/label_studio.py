# ml_backend/infrastructure/label_studio.py
import requests
from domain.errors import ExternalServiceError


def save_predictions_to_labelstudio(
    label_studio_url: str,
    token: str,
    model_version: str,
    task_id: str,
    prediction_result: list,
) -> None:
    payload = {
        "task": task_id,
        "model_version": model_version,
        "result": prediction_result,
    }
    try:
        response = requests.post(
            f"{label_studio_url}/api/predictions",
            headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNREACHABLE",
            message="Could not save predictions to Label Studio.",
            meta={"error": str(e)},
        )


def attach_meta_to_task(
    label_studio_url: str,
    token: str,
    task_id: int,
    meta: dict,
) -> None:
    try:
        r = requests.get(
            f"{label_studio_url}/api/tasks/{task_id}",
            headers={"Authorization": f"Token {token}"},
            timeout=15,
        )
        r.raise_for_status()
        task = r.json()
        data = task.get("data") or {}
        data["ml_meta"] = meta

        pr = requests.patch(
            f"{label_studio_url}/api/tasks/{task_id}",
            headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
            json={"data": data},
            timeout=15,
        )
        pr.raise_for_status()
    except requests.RequestException as e:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNREACHABLE",
            message="Could not attach meta to Label Studio task.",
            meta={"error": str(e)},
        )
