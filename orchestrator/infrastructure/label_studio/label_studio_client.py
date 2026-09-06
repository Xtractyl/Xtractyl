# orchestrator/infrastructure/label_studio/label_studio_client.py

import os

import requests
from domain.errors import ExternalServiceError
from infrastructure.interfaces.label_studio import LabelStudioInterface

LABELSTUDIO_HOST = os.getenv("LABELSTUDIO_CONTAINER_NAME", "labelstudio")
LABELSTUDIO_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LABEL_STUDIO_URL = f"http://{LABELSTUDIO_HOST}:{LABELSTUDIO_PORT}"
ML_BACKEND_HOST = os.getenv("ML_BACKEND_CONTAINER_NAME", "ml_backend")
ML_BACKEND_PORT = os.getenv("ML_BACKEND_PORT", "6789")
ML_BACKEND_URL = f"http://{ML_BACKEND_HOST}:{ML_BACKEND_PORT}"

BATCH_SIZE = 50


class LabelStudioClient(LabelStudioInterface):
    def create_project(self, title: str, label_config: str, token: str) -> int:
        headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        try:
            response = requests.post(
                f"{LABEL_STUDIO_URL}/api/projects",
                headers=headers,
                json={"title": title, "label_config": label_config},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            raise ExternalServiceError(
                code="LABEL_STUDIO_UNAVAILABLE",
                message="Label Studio project creation failed.",
            )
        project_id = response.json().get("id")
        if not project_id:
            raise ExternalServiceError(
                code="LABEL_STUDIO_UNAVAILABLE",
                message="Label Studio project creation failed.",
            )
        return project_id

    def attach_ml_backend(self, project_id: int, token: str) -> None:
        headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        try:
            ml_response = requests.post(
                f"{LABEL_STUDIO_URL}/api/ml",
                headers=headers,
                json={"url": ML_BACKEND_URL, "title": "xtractyl-backend", "project": project_id},
                timeout=20,
            )
            ml_response.raise_for_status()
        except requests.RequestException:
            raise ExternalServiceError(
                code="ML_BACKEND_UNAVAILABLE",
                message="Could not attach ML backend to project.",
            )

    def upload_tasks(self, project_id: int, tasks: list, token: str) -> None:
        headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks/bulk"
        for i in range(0, len(tasks), BATCH_SIZE):
            batch = tasks[i : i + BATCH_SIZE]
            try:
                resp = requests.post(url, headers=headers, json=batch, timeout=30)
                resp.raise_for_status()
            except requests.RequestException:
                raise ExternalServiceError(
                    code="LABEL_STUDIO_UNAVAILABLE",
                    message=f"Task upload failed at batch {i}.",
                )

    def list_projects(self, token: str) -> list[dict]:
        """Returns every Label Studio project visible to this token,
        Backs the orphan sweep in domain/cleanup.py that removes
        any project in label studio without matching projects.label_studio_id row"""
        headers = {"Authorization": f"Token {token}"}
        url = f"{LABEL_STUDIO_URL}/api/projects"
        results: list[dict] = []
        while url:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                raise ExternalServiceError(
                    code="LABEL_STUDIO_UNAVAILABLE",
                    message="Could not list Label Studio projects.",
                )
            data = response.json()
            page = data if isinstance(data, list) else data.get("results", [])
            results.extend(page)
            url = data.get("next") if isinstance(data, dict) else None
        return results

    def delete_project(self, project_id: int, token: str) -> None:
        headers = {"Authorization": f"Token {token}"}
        try:
            response = requests.delete(
                f"{LABEL_STUDIO_URL}/api/projects/{project_id}",
                headers=headers,
                timeout=20,
            )
            if response.status_code == 404:
                # Already gone — deleting an orphan is idempotent, not an error.
                return
            response.raise_for_status()
        except requests.RequestException:
            raise ExternalServiceError(
                code="LABEL_STUDIO_UNAVAILABLE",
                message=f"Could not delete Label Studio project {project_id}.",
            )
