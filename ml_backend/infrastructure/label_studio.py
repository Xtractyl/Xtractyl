# ml_backend/infrastructure/label_studio.py
import os

import requests
from domain.errors import ExternalServiceError

LS_HOST = os.getenv("LABELSTUDIO_HOST", "labelstudio")
LS_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LS_BASE = os.getenv("LS_BASE", f"http://{LS_HOST}:{LS_PORT}")


def save_predictions_to_labelstudio(
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
            f"{LS_BASE}/api/predictions",
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
