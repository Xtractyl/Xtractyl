# orchestrator/routes/groundtruth_qal.py

import json
import os

GROUNDTRUTH_QAL_PATH = os.getenv(
    "GROUNDTRUTH_QAL_PATH",
    "/app/data/projects/Evaluation_Set_Do_Not_Delete/questions_and_labels.json",
)


def get_groundtruth_qal():
    """
    Return the questions_and_labels.json content for the groundtruth project.
    """
    with open(GROUNDTRUTH_QAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
