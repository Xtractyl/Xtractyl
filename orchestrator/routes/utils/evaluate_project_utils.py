import os
import json
import requests

LABEL_STUDIO_URL = (
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:"
    f"{os.getenv('LABELSTUDIO_PORT', '8080')}"
)

SPECIAL_PROJECT_TITLE = "Evaluation_Set_Do_Not_Delete"


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def create_evaluation_project(token: str) -> int:
    """
    Legt das Standard-Evaluationsprojekt 'Evaluation_Set_Do_Not_Delete'
    in Label Studio an, basierend auf einem GUI-Task-Export
    (Liste von Tasks mit annotations/result/...).
    """
    eval_path = "/app/data/labelstudio_Evaluation_Set_Do_Not_Delete/Evaluation_Set.json"

    if not os.path.exists(eval_path):
        raise RuntimeError(f"Evaluation project JSON not found at: {eval_path}")

    with open(eval_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Wir erwarten hier explizit eine LISTE von Tasks (GUI-Export)
    if not isinstance(raw, list):
        raise RuntimeError(
            "Evaluation_Set.json is expected to be a list of tasks (Label Studio task export)."
        )

    tasks = raw

    # Labels aus den Annotationen sammeln, z. B. "Patient", ...
    labels_set = set()
    for task in tasks:
        for ann in task.get("annotations", []):
            for res in ann.get("result", []):
                for lab in res.get("value", {}).get("labels", []):
                    labels_set.add(lab)

    if not labels_set:
        raise RuntimeError("No labels found in Evaluation_Set.json (value.labels).")

    # label_config dynamisch aus den Labelnamen bauen
    labels_xml = "".join(f'<Label value="{l}"/>' for l in sorted(labels_set))

    label_config = f"""
    <View>
      <HyperText name="html" value="$html"/>
      <Labels name="label" toName="html">
        {labels_xml}
      </Labels>
    </View>
    """.strip()

    # 1) Projekt in Label Studio anlegen
    create_payload = {
        "title": SPECIAL_PROJECT_TITLE,
        "description": "Auto-created standard evaluation project for Xtractyl Evaluate AI.",
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

    # 2) Tasks importieren
    import_resp = requests.post(
        f"{LABEL_STUDIO_URL}/api/projects/{project_id}/import",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json=tasks,
        timeout=60,
    )
    import_resp.raise_for_status()

    return project_id