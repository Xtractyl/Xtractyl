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


def _fetch_tasks_page(
    token: str, project_id: int, limit: int = 0, offset: int = 0
) -> Tuple[List[dict], int]:
    """
    Fetch all tasks (including predictions) for a project — without pagination.
    Works for both dict and list responses from Label Studio.
    """
    headers = _auth_headers(token)
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks"
    params = {"fields": "all",
              "include": "predictions,annotations"}

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


def _fetch_task_annotations(token: str, task_id: int) -> List[dict]:
    url = f"{LABEL_STUDIO_URL}/api/tasks/{task_id}/annotations"
    r = requests.get(url, headers=_auth_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def _prediction_map(task: dict) -> dict:
    """
    For each *label class* (e.g., 'DateOfBirth', 'Patient', ...), return two columns:
      <class>__pred = raw text span(s) from latest prediction
      <class>__ann  = raw text span(s) from ground-truth annotation if present,
                      else from latest annotation.

    Non-'labels' tools fall back to from_name, also paired as __pred/__ann.
    Cell values are joined by " | " if multiple spans exist.
    """

    def _bucket_from_results(results: list) -> dict:
        bucket = defaultdict(list)

        for r in results or []:
            typ = r.get("type")
            from_name = r.get("from_name") or r.get("name") or "field"
            val = r.get("value", {}) or {}

            if typ == "labels":
                labels = val.get("labels")
                text = val.get("text", "")
                labels = (
                    labels if isinstance(labels, list)
                    else [labels] if isinstance(labels, str)
                    else []
                )
                for cls in labels:
                    col = str(cls)
                    bucket[col].append(str(text) if text is not None else "")
            else:
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
                    if isinstance(val, dict) and len(val) == 1:
                        v = next(iter(val.values()))
                        bucket[str(from_name)].append(str(v))

        return {k: " | ".join(v for v in vs if v is not None) for k, vs in bucket.items()}

    # ---------- latest prediction ----------
    preds = task.get("predictions") or []
    preds = [p for p in preds if isinstance(p, dict)]
    if preds:
        preds_sorted = sorted(
            preds,
            key=lambda p: p.get("created_at") or p.get("updated_at") or "",
            reverse=True,
        )
        chosen_pred = preds_sorted[0]
        pred_bucket = _bucket_from_results(chosen_pred.get("result") or [])
    else:
        pred_bucket = {}

    # ---------- ground-truth / latest annotation ----------
    anns = task.get("annotations") or []
    anns = [a for a in anns if isinstance(a, dict)]
    if anns:
        gt_anns = [a for a in anns if a.get("ground_truth") is True]
        ann_candidates = gt_anns if gt_anns else anns
        ann_sorted = sorted(
            ann_candidates,
            key=lambda a: a.get("created_at") or a.get("updated_at") or "",
            reverse=True,
        )
        chosen_ann = ann_sorted[0]
        ann_bucket = _bucket_from_results(chosen_ann.get("result") or [])
    else:
        ann_bucket = {}

    # ---------- pair columns ----------
    all_cols = set(pred_bucket.keys()) | set(ann_bucket.keys())
    out = {}
    for col in sorted(all_cols):
        out[f"{col}__pred"] = pred_bucket.get(col, "")
        out[f"{col}__ann"] = ann_bucket.get(col, "")
    return out


def build_results_table(token: str, project_name: str, limit: int = 50, offset: int = 0) -> dict:
    project_id = _resolve_project_id(token, project_name)
    tasks, total = _fetch_tasks_page(token, project_id, limit=limit, offset=offset)

    label_columns: List[str] = []
    rows_proto: List[Dict[str, Any]] = []

    for t in tasks:
        data = t.get("data") or {}
        filename = data.get("name", "")  

        anns = t.get("annotations") or []
        # Bulk liefert nur [{}] oder leere result → dann nachladen
        if not any(a and (a.get("result") or []) for a in anns):
            t["annotations"] = _fetch_task_annotations(token, t["id"])

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

    return {"columns": columns, "rows": rows, "total": int(total)}
