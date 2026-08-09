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
