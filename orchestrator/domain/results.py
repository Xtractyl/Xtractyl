# orchestrator/domain/results.py
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from domain.models.results import GetResultsTableCommand

from .utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    resolve_project_id,
)

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "/app/data/results"))


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
                    labels
                    if isinstance(labels, list)
                    else [labels]
                    if isinstance(labels, str)
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


def _format_cell(value) -> str:
    # exakt wie dein Frontend formatCell()
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def _write_results_table_csv(
    columns: list[str], rows: list[dict], project_id: int, project_name: str
) -> str:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "".join(
        c if c.isalnum() or c in "-_." else "_" for c in (project_name or "project")
    )[:80]
    out = RESULTS_DIR / f"results_{safe_name}_pid{project_id}_{ts}.csv"

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for row in rows:
            w.writerow([_format_cell(row.get(col)) for col in columns])

    return str(out)


def build_results_table(cmd: GetResultsTableCommand):
    token = cmd.token
    project_name = cmd.project_name
    project_id = resolve_project_id(token, project_name)
    tasks, total = fetch_tasks_page(token, project_id)

    label_columns: List[str] = []
    rows_proto: List[Dict[str, Any]] = []

    for t in tasks:
        data = t.get("data") or {}
        filename = data.get("name", "")

        anns = t.get("annotations") or []
        # Bulk liefert nur [{}] oder leere result → dann nachladen
        if not any(a and (a.get("result") or []) for a in anns):
            t["annotations"] = fetch_task_annotations(token, t["id"])

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
    payload = {"columns": columns, "rows": rows, "total": int(total)}
    payload["results_output_path_csv"] = _write_results_table_csv(
        columns, rows, project_id, project_name
    )
    return payload
