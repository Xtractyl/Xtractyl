import os
import csv
import hashlib
import requests
from collections import defaultdict
from dotenv import load_dotenv
from sklearn.metrics import precision_recall_fscore_support

load_dotenv()

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://labelstudio:8080")
LABEL_STUDIO_TOKEN = os.getenv("LABEL_STUDIO_API_TOKEN")
HEADERS = {"Authorization": f"Token {LABEL_STUDIO_TOKEN}"}

PROJECT_ID_PRED = os.getenv("LABEL_STUDIO_PROJECT_ID_PRED")  # Modell
PROJECT_ID_GT = os.getenv("LABEL_STUDIO_PROJECT_ID_GT")      # Ground Truth
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma:latest").replace(":", "_")

SAVE_PATH = f"/app/evaluation/{PROJECT_ID_PRED}_vs_{PROJECT_ID_GT}"
os.makedirs(SAVE_PATH, exist_ok=True)
csv_path = os.path.join(SAVE_PATH, f"{MODEL_NAME}_comparison.csv")
txt_path = os.path.join(SAVE_PATH, f"{MODEL_NAME}_metrics.txt")

def fetch_tasks(project_id):
    page = 1
    all_tasks = []
    while True:
        url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks?page={page}&page_size=100"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 404:
            break
        r.raise_for_status()
        page_tasks = r.json()
        if not page_tasks:
            break
        all_tasks.extend(page_tasks)
        page += 1
    return all_tasks

def get_html_hash(task):
    html = task.get("data", {}).get("html", "")
    return hashlib.md5(html.encode("utf-8")).hexdigest() if html else None

def extract_labels(result_list):
    return {
        res["value"]["labels"][0]: res["value"]["text"]
        for res in result_list
        if "labels" in res["value"] and "text" in res["value"]
    }

def compare_by_html(pred_tasks, gt_tasks):
    pred_map = {
        get_html_hash(task): task
        for task in pred_tasks
        if task.get("annotations")
    }
    gt_map = {
        get_html_hash(task): task
        for task in gt_tasks
        if task.get("annotations")
    }

    common_hashes = set(pred_map) & set(gt_map)
    print(f"🔗 Übereinstimmende HTML-Hashes: {len(common_hashes)}")

    rows = []
    labels_set = set()

    for h in common_hashes:
        pred_task = pred_map[h]
        gt_task = gt_map[h]

        pred_result = extract_labels(pred_task["annotations"][0].get("result", []))
        gt_result = extract_labels(gt_task["annotations"][0].get("result", []))

        labels_set.update(pred_result.keys())
        labels_set.update(gt_result.keys())

        row = {
            "task_id_prediction": pred_task["id"],
            "task_id_annotation": gt_task["id"]
        }
        for label in labels_set:
            row[f"{label}_prediction"] = pred_result.get(label, "")
            row[f"{label}_annotation"] = gt_result.get(label, "")
        rows.append(row)

    return rows, sorted(labels_set)

def calculate_metrics(rows, labels):
    all_preds, all_anns = [], []
    per_label_data = defaultdict(lambda: {"preds": [], "anns": []})

    for row in rows:
        for label in labels:
            pred = row.get(f"{label}_prediction", "").strip()
            ann = row.get(f"{label}_annotation", "").strip()

            match = pred == ann and pred != ""
            all_preds.append(1 if match else 0)
            all_anns.append(1)

            per_label_data[label]["preds"].append(1 if match else 0)
            per_label_data[label]["anns"].append(1)

    txt_lines = []
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_anns, all_preds, average="binary", zero_division=0
    )

    txt_lines.append("== Overall Metrics ==")
    txt_lines.append(f"Precision: {round(precision, 3)}")
    txt_lines.append(f"Recall:    {round(recall, 3)}")
    txt_lines.append(f"F1:        {round(f1, 3)}\n")

    txt_lines.append("== Per Label ==")
    for label in labels:
        y_true = per_label_data[label]["anns"]
        y_pred = per_label_data[label]["preds"]
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )
        txt_lines.append(f"{label}:")
        txt_lines.append(f"  Precision: {round(p, 3)}")
        txt_lines.append(f"  Recall:    {round(r, 3)}")
        txt_lines.append(f"  F1:        {round(f1, 3)}\n")

    return txt_lines

def main():
    print(f"📥 Lade Tasks aus Prediction-Projekt: {PROJECT_ID_PRED}")
    pred_tasks = fetch_tasks(PROJECT_ID_PRED)
    print(f"📥 Lade Tasks aus Ground-Truth-Projekt: {PROJECT_ID_GT}")
    gt_tasks = fetch_tasks(PROJECT_ID_GT)

    print(f"🔢 Annotierte Prediction-Tasks: {sum(bool(t.get('annotations')) for t in pred_tasks)}")
    print(f"🔢 Annotierte Ground-Truth-Tasks: {sum(bool(t.get('annotations')) for t in gt_tasks)}")

    rows, labels = compare_by_html(pred_tasks, gt_tasks)

    fieldnames = ["task_id_prediction", "task_id_annotation"]
    for label in labels:
        fieldnames += [f"{label}_prediction", f"{label}_annotation"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    txt_lines = calculate_metrics(rows, labels)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))

    print(f"✅ Vergleich gespeichert unter:\n- CSV: {csv_path}\n- Metriken: {txt_path}")

if __name__ == "__main__":
    main()