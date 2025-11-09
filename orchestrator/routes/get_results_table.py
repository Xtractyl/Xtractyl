import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import requests

LABEL_STUDIO_URL = os.getenv(
    "LABEL_STUDIO_URL",
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}",
)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def _resolve_project_id(token: str, project_name: str) -> int:
    url = f"{LABEL_STUDIO_URL}/api/projects"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    projects = r.json()
    if isinstance(projects, dict) and "results" in projects:
        projects = projects["results"]
    for p in projects:
        if p.get("title") == project_name:
            return int(p["id"])
    raise ValueError(f'Project "{project_name}" not found')


def _fetch_tasks_page(token: str, project_id: int, limit: int = 0, offset: int = 0) -> Tuple[List[dict], int]:
    """
    Fetch all tasks (including predictions) for a project — without pagination.
    Works for both dict and list responses from Label Studio.
    """
    headers = _auth_headers(token)
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks"
    params = {"include": "predictions"}
    
    r = requests.get(url, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    if isinstance(data, dict) and "results" in data:
        tasks = data.get("results", [])
        total = int(data.get("count", len(tasks)))
    elif isinstance(data, list):
        tasks = data
        total = len(tasks)
    else:
        tasks = []
        total = 0

    return tasks, total


def _prediction_map(task: dict) -> dict:
    """
    One column per *label class* (e.g., 'dateofbirth', 'Patient', ...).
    Cell = raw text span(s) for that class, joined by " | " if multiple.
    Other non-'labels' tools fallback to from_name without normalization.
    """
    preds = task.get("predictions") or []
    if not preds:
        return {}

    # pick latest prediction
    preds_sorted = sorted(
        preds, key=lambda p: p.get("created_at") or p.get("updated_at") or "", reverse=True
    )
    chosen = preds_sorted[0]
    results = chosen.get("result") or []

    bucket = defaultdict(list)

    for r in results:
        typ = r.get("type")
        from_name = r.get("from_name") or r.get("name") or "field"
        val = r.get("value", {}) or {}

        if typ == "labels":
            # create one column per class; put raw value.text into that column
            labels = val.get("labels")
            text = val.get("text", "")
            labels = (
                labels if isinstance(labels, list) else [labels] if isinstance(labels, str) else []
            )
            for cls in labels:
                col = str(cls)
                bucket[col].append(str(text) if text is not None else "")
        else:
            # generic fallback for other tools: use from_name as column, raw scalar where possible
            if "choices" in val and isinstance(val["choices"], list):
                bucket[str(from_name)].append(", ".join(map(str, val["choices"])))
            elif "text" in val and isinstance(val["text"], list):
                bucket[str(from_name)].append("\n".join(map(str, val["text"])))
            elif isinstance(val.get("text"), str):
                bucket[str(from_name)].append(val["text"])
            elif "number" in val:
                bucket[str(from_name)].append(str(val["number"]))
            elif "rating" in val:
                bucket[str(from_name)].append(str(val["rating"]))
            else:
                # last-resort: single-key dict → stringify
                if isinstance(val, dict) and len(val) == 1:
                    v = next(iter(val.values()))
                    bucket[str(from_name)].append(str(v))

    # join multiples per column
    return {k: " | ".join(v for v in vs if v is not None) for k, vs in bucket.items()}


def build_results_table(token: str, project_name: str, limit: int = 50, offset: int = 0) -> dict:
    project_id = _resolve_project_id(token, project_name)
    tasks, total = _fetch_tasks_page(token, project_id, limit=limit, offset=offset)

    label_columns: List[str] = []
    rows_proto: List[Dict[str, Any]] = []

    for t in tasks:
        data = t.get("data") or {}
        filename = data.get("name", "")  # simplified: always use 'name'
        pred_map = _prediction_map(t)
        rows_proto.append(
            {
                "task_id": t.get("id"),
                "filename": filename,
                "labels": pred_map,
            }
        )
        for k in pred_map.keys():
            if k not in label_columns:
                label_columns.append(k)

    columns = ["task_id", "filename"] + label_columns

    rows: List[Dict[str, Any]] = []
    for r in rows_proto:
        flat = {"task_id": r["task_id"], "filename": r["filename"]}
        for col in label_columns:
            flat[col] = r["labels"].get(col, "")
        rows.append(flat)

    return {
        "columns": columns,
        "rows": rows,
        "total": int(total)
    }
