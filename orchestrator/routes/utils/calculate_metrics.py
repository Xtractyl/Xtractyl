# orchestrator/routes/utils/calculate_metrics.py
from __future__ import annotations

from typing import Dict, List


def compute_metrics_from_rows(
    gt_rows: List[dict],
    pred_rows: List[dict],
    filename_key: str = "filename",
    labels_key: str = "labels",
) -> dict:
    """
    Strict literal equality evaluation.

    Expects rows shaped like:
      {"filename": "...", "labels": {"Patient": "John", "TNM": "T2", ...}}

    For each (filename, label):
      - TP if both present and identical
      - FP+FN if both present but different (wrong extraction counts as both)
      - FN if GT present, pred missing
      - FP if pred present, GT missing
      - TN if both missing

    Returns:
      {
        "micro": {...},
        "per_label": {label: {tp,fp,fn,tn}}
        "filenames_count": len(all_filenames),
        "task_metrics": [task_metrics_by_fn[fn] for fn in all_filenames],
      }
    """
    gt_by_fn = {r.get(filename_key): r for r in gt_rows if r.get(filename_key)}
    pred_by_fn = {r.get(filename_key): r for r in pred_rows if r.get(filename_key)}

    pred_meta_by_fn = {
        r.get(filename_key): (r.get("meta") or {})
        for r in pred_rows
        if r.get(filename_key)
    }
    
    all_filenames = sorted(set(gt_by_fn.keys()) | set(pred_by_fn.keys()))
    all_labels = set()
    for r in gt_rows:
        all_labels |= set((r.get(labels_key) or {}).keys())
    for r in pred_rows:
        all_labels |= set((r.get(labels_key) or {}).keys())
    all_labels = sorted(all_labels)

    per_label: Dict[str, dict] = {}
    task_metrics_by_fn: Dict[str, dict] = {}

    TP = FP = FN = TN = 0

    for lab in all_labels:
        tp = fp = fn = tn = 0

        for fnm in all_filenames:
            if fnm not in task_metrics_by_fn:
                task_metrics_by_fn[fnm] = {
                    "filename": fnm,
                    "meta": pred_meta_by_fn.get(fnm, {}),  # 👈 HIER
                    "per_label": {},
                    "counts": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
                }

            gt_val = ((gt_by_fn.get(fnm, {}) or {}).get(labels_key) or {}).get(lab, "")
            pr_val = ((pred_by_fn.get(fnm, {}) or {}).get(labels_key) or {}).get(lab, "")

            gt_present = bool(gt_val)
            pr_present = bool(pr_val)

            if gt_present and pr_present:
                if gt_val == pr_val:
                    tp += 1
                    status = "tp"
                    task_metrics_by_fn[fnm]["counts"]["tp"] += 1
                else:
                    # wrong value: counts as miss + spurious
                    fp += 1
                    fn += 1
                    status = "fp_fn"
                    task_metrics_by_fn[fnm]["counts"]["fp"] += 1
                    task_metrics_by_fn[fnm]["counts"]["fn"] += 1
            elif gt_present and not pr_present:
                fn += 1
                status = "fn"
                task_metrics_by_fn[fnm]["counts"]["fn"] += 1
            elif (not gt_present) and pr_present:
                fp += 1
                status = "fp"
                task_metrics_by_fn[fnm]["counts"]["fp"] += 1
            else:
                tn += 1
                status = "tn"
                task_metrics_by_fn[fnm]["counts"]["tn"] += 1
            task_metrics_by_fn[fnm]["per_label"][lab] = {
                "gt": gt_val,
                "pred": pr_val,
                "status": status,
            }

        TP += tp
        FP += fp
        FN += fn
        TN += tn

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        per_label[lab] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    precision = TP / (TP + FP) if (TP + FP) else 0.0
    recall = TP / (TP + FN) if (TP + FN) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (TP + TN) / (TP + FP + FN + TN) if (TP + FP + FN + TN) else 0.0

    return {
        "micro": {
            "tp": TP,
            "fp": FP,
            "fn": FN,
            "tn": TN,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
        },
        "per_label": per_label,
        "labels": all_labels,
        "filenames_count": len(all_filenames),
        "task_metrics": [task_metrics_by_fn[fn] for fn in all_filenames],
    }
