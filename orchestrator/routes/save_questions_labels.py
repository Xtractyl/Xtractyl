import os
import json

def save_questions_and_labels_main(payload):
    logs = []

    project_name = payload.get("title")
    questions = payload.get("questions", [])
    labels = payload.get("labels", [])

    if not project_name:
        raise ValueError("No project name provided.")

    project_folder = os.path.join("..", "data", "projects", project_name)
    os.makedirs(project_folder, exist_ok=True)

    filepath = os.path.join(project_folder, "questions_and_labels.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "questions": questions,
            "labels": labels
        }, f, ensure_ascii=False, indent=2)

    logs.append(f"✅ questions_and_labels.json gespeichert unter {filepath}")
    return logs