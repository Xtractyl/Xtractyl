# orchestrator/routes/utils/calculate_metrics.py
from __future__ import annotations

from typing import Dict, List


def _avg(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _p95(xs: List[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = max(0, min(len(s) - 1, int(round(0.95 * (len(s) - 1)))))
    return float(s[i])


def compute_metrics_from_rows(
    gt_rows: List[dict],
    pred_rows: List[dict],
    labels: List[str],
) -> dict:
    """
     Strict literal equality evaluation.

    Expects gt rows shaped like:
       {"html_hash": "...", "filename": "...", "labels": {"Patient": "John", "TNM": "T2", ...}}

    and pred rows shaped like:
      {"html_hash": "...", "filename": "...", "labels": {"Patient": "John", "TNM": "T2", ...},
       "dom_match_by_label": {"Patient": True, "TNM": None, ...},
       "task_ms_total": 1200.0, "task_ms_llm_total": 900.0,
       "task_ms_dom_extract": 200.0, "task_ms_dom_match": 100.0}


    Rows of gt_rows and pred_rows are matched by `html_hash` (the content of the
    document), not by filename. Both lists must contain exactly the same html_hash
    values, each at most once per list, otherwise ValueError. `filename` is only
    used for display and is taken from the gt row.

    `labels` is the label set of the project (single source of truth). Every
     label in it is evaluated for every file, even if it occurs in no row. A row
     containing a label that is not in `labels` raises ValueError.

    For each (html_hash, label):
       - TP if both present and identical
       - FP+FN if both present but different (wrong extraction counts as both)
       - FN if GT present, pred missing
       - FP if pred present, GT missing
       - TN if GT missing and pred is the literal <<<NO_MATCH>>> sentinel
       - FP if GT missing and pred is falsy but NOT the sentinel (empty
         string [seems currently impossible for an LLM to actively provide a blank answer],
         None [seems currently impossible for an LLM to actively provide a blank answer without error],
         missing key) — the model failed to signal no-match
         via the required sentinel convention, which is itself a real,
         countable error

     Returns:
       {
         "micro": {...},
         "per_label": {label: {tp,fp,fn,tn}}
         "filenames_count": len(all_hashes),
         "task_metrics": [task_metrics_by_hash[h] for h in all_hashes],
       }
    """
    gt_by_hash = {r["html_hash"]: r for r in gt_rows}
    pred_by_hash = {r["html_hash"]: r for r in pred_rows}
    if len(gt_by_hash) != len(gt_rows) or len(pred_by_hash) != len(pred_rows):
        raise ValueError("an html_hash occurs more than once in gt_rows or in pred_rows")

    if gt_by_hash.keys() != pred_by_hash.keys():
        raise ValueError(
            "gt_rows and pred_rows must contain the same html_hash values: "
            f"only in gt: {sorted(gt_by_hash.keys() - pred_by_hash.keys())}, "
            f"only in pred: {sorted(pred_by_hash.keys() - gt_by_hash.keys())}"
        )
    all_hashes = sorted(gt_by_hash, key=lambda h: gt_by_hash[h]["filename"])
    all_labels = sorted(labels)

    labels_in_rows = set()
    for r in gt_rows + pred_rows:
        labels_in_rows |= set((r.get("labels") or {}).keys())
    unknown_labels = sorted(labels_in_rows - set(all_labels))
    if unknown_labels:
        raise ValueError(f"rows contain labels not defined for the project: {unknown_labels}")

    per_label: Dict[str, dict] = {}
    task_metrics_by_hash: Dict[str, dict] = {}

    TP = FP = FN = TN = 0
    perf_task_ms_total: List[float] = []
    perf_task_ms_llm_total: List[float] = []
    perf_task_ms_dom_extract: List[float] = []
    perf_task_ms_dom_match: List[float] = []
    n_tasks_with_perf = 0

    for lab in all_labels:
        tp = fp = fn = tn = 0
        for html_hash in all_hashes:
            if html_hash not in task_metrics_by_hash:
                task_metrics_by_hash[html_hash] = {
                    "filename": gt_by_hash[html_hash]["filename"],
                    "per_label": {},
                    "counts": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
                }

            # collect perf once per task (not per label)
            if not task_metrics_by_hash[html_hash].get("_perf_collected"):
                pred = pred_by_hash[html_hash]
                perf_task_ms_total.append(float(pred["task_ms_total"]))
                perf_task_ms_llm_total.append(float(pred["task_ms_llm_total"]))
                perf_task_ms_dom_extract.append(float(pred["task_ms_dom_extract"]))
                perf_task_ms_dom_match.append(float(pred["task_ms_dom_match"]))
                n_tasks_with_perf += 1
                task_metrics_by_hash[html_hash]["_perf_collected"] = True

            gt_val = (gt_by_hash[html_hash].get("labels") or {}).get(lab, "")
            pr_val = (pred_by_hash[html_hash].get("labels") or {}).get(lab, "")

            gt_present = bool(gt_val)
            pr_no_match = pr_val == "<<<NO_MATCH>>>"
            pr_present = bool(pr_val) and not pr_no_match

            if gt_present and pr_present:
                if gt_val == pr_val:
                    tp += 1
                    status = "tp"
                    task_metrics_by_hash[html_hash]["counts"]["tp"] += 1
                else:
                    fp += 1
                    fn += 1
                    status = "fp_fn"
                    task_metrics_by_hash[html_hash]["counts"]["fp"] += 1
                    task_metrics_by_hash[html_hash]["counts"]["fn"] += 1

            elif gt_present and not pr_present:
                fn += 1
                status = "fn"
                task_metrics_by_hash[html_hash]["counts"]["fn"] += 1

            elif (not gt_present) and pr_present:
                fp += 1
                status = "fp"
                task_metrics_by_hash[html_hash]["counts"]["fp"] += 1

            elif (not gt_present) and pr_no_match:
                tn += 1
                status = "tn"
                task_metrics_by_hash[html_hash]["counts"]["tn"] += 1

            else:
                # not gt_present, and pr_val is falsy but NOT the literal
                # <<<NO_MATCH>>> sentinel (empty string, None, missing key).
                # this would require an LLM to provide
                # an empty answer or return something falsy without producing an error
                # so it is a secuirty measure for something that seems impossible
                fp += 1
                status = "fp"
                task_metrics_by_hash[html_hash]["counts"]["fp"] += 1

            task_metrics_by_hash[html_hash]["per_label"][lab] = {
                "gt": gt_val,
                "pred": pr_val,
                "dom_match": pred_by_hash[html_hash]["dom_match_by_label"][lab],
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

    performance = {
        "n_tasks_with_perf": n_tasks_with_perf,
        "task_ms_total_sum": sum(perf_task_ms_total),
        "task_ms_total_avg": _avg(perf_task_ms_total),
        "task_ms_total_p95": _p95(perf_task_ms_total),
        "task_ms_llm_total_sum": sum(perf_task_ms_llm_total),
        "task_ms_llm_total_avg": _avg(perf_task_ms_llm_total),
        "task_ms_llm_total_p95": _p95(perf_task_ms_llm_total),
        "task_ms_dom_extract_sum": sum(perf_task_ms_dom_extract),
        "task_ms_dom_extract_avg": _avg(perf_task_ms_dom_extract),
        "task_ms_dom_match_sum": sum(perf_task_ms_dom_match),
        "task_ms_dom_match_avg": _avg(perf_task_ms_dom_match),
    }

    # remove internal guard flags from output
    for t in task_metrics_by_hash.values():
        t.pop("_perf_collected", None)

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
        "filenames_count": len(all_hashes),
        "task_metrics": [task_metrics_by_hash[h] for h in all_hashes],
        "performance": performance,
    }
