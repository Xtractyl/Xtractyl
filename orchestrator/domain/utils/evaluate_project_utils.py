# /orchestrator/routes/utils/evaluate_project_utils.py
import json
import os
from pathlib import Path

import requests

GROUNDTRUTH_QAL_DIR = Path(
    os.getenv(
        "GROUNDTRUTH_QAL_DIR",
        "/app/data/projects/Evaluation_Sets_Do_Not_Delete",
    )
)

LABEL_STUDIO_URL = (
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:"
    f"{os.getenv('LABELSTUDIO_PORT', '8080')}"
)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def create_evaluation_project(token: str, gt_set_name: str) -> int:
    """
    Create an evaluation project in Label Studio based on a GUI task export
    found in the corresponding GT set folder.
    """
    eval_path = GROUNDTRUTH_QAL_DIR / gt_set_name / "Evaluation_Set.json"

    if not eval_path.exists():
        raise RuntimeError(f"Evaluation project JSON not found at: {eval_path}")

    with open(eval_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Wir erwarten hier explizit eine LISTE von Tasks (GUI-Export)
    if not isinstance(raw, list):
        raise RuntimeError(
            "Evaluation_Set.json is expected to be a list of tasks (Label Studio task export)."
        )

    tasks = raw

    # collect labels from annotations
    labels_set = set()
    for task in tasks:
        for ann in task.get("annotations", []):
            for res in ann.get("result", []):
                for lab in res.get("value", {}).get("labels", []):
                    labels_set.add(lab)

    if not labels_set:
        raise RuntimeError(f"No labels found in Evaluation_Set.json for set: {gt_set_name}")

    # build label_config dynamically from label names
    labels_xml = "".join(f'<Label value="{label}"/>' for label in sorted(labels_set))

    label_config = f"""
    <View>
      <HyperText name="html" value="$html"/>
      <Labels name="label" toName="html">
        {labels_xml}
      </Labels>
    </View>
    """.strip()

    # 1) create evaluation project if it has accidentally been removed
    create_payload = {
        "title": gt_set_name,
        "description": f"Auto-created evaluation project for GT set: {gt_set_name}",
        "label_config": label_config,
    }

    resp = requests.post(
        f"{LABEL_STUDIO_URL}/api/projects",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json=create_payload,
        timeout=20,
    )
    resp.raise_for_status()
    project_id = int(resp.json()["id"])

    # 2) import tasks
    import_resp = requests.post(
        f"{LABEL_STUDIO_URL}/api/projects/{project_id}/import",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json=tasks,
        timeout=60,
    )
    import_resp.raise_for_status()

    return project_id
