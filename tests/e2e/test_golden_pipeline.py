# tests/e2e/test_golden_pipeline.py
import os
import time
import pathlib
import requests
import pytest
import shutil
import json
from urllib.parse import urljoin
import uuid 
from fixtures.endpoints_adapter import orch, doc

INPUT_DIR = pathlib.Path(os.getenv("TEST_INPUT_DIR", "/opt/input_pdfs"))
ORCH_TIMEOUT = int(os.getenv("ORCH_TIMEOUT_SECONDS", "120"))
DOCLING_TIMEOUT = int(os.getenv("DOCLING_TIMEOUT_SECONDS", "1800"))
PRELABEL_TIMEOUT = int(os.getenv("PRELABEL_TIMEOUT_SECONDS", "900"))


LS_TOKEN = os.getenv("LABEL_STUDIO_LEGACY_TOKEN") or os.getenv("LS_LEGACY_TOKEN")
TEST_MODEL = os.getenv("TEST_MODEL", "llama3.1:8b")
PROJECT_NAME = os.getenv("E2E_PROJECT_NAME", "e2e_golden_pipeline")

# Docling container paths
PDFS_DIR = pathlib.Path("/pdfs")
HTMLS_DIR = pathlib.Path("/htmls")
PROJECTS_DIR = pathlib.Path("/projects")

LABELSTUDIO_HOST = os.getenv("LABELSTUDIO_CONTAINER_NAME", "labelstudio")
LABELSTUDIO_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LABEL_STUDIO_URL = f"http://{LABELSTUDIO_HOST}:{LABELSTUDIO_PORT}"

REF_DIR = pathlib.Path("/opt/tests/e2e/data/ground_truth_and_baseline_results")
REF_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_PATH = REF_DIR / "baseline_predictions.json"
GROUNDTRUTH_PATH = REF_DIR / "ground_truth.json"
REGEN_BASELINE = os.getenv("REGEN_BASELINE", "").lower() in {"1","true","yes"}

SYSTEM_PROMPT = """You are a pure extraction model.

        When you are given a TEXT and a QUESTION, you must return exactly one literal text passage from the TEXT that best answers the QUESTION.

        Output format (mandatory):
        - Return EXACTLY ONE matching passage, with no introduction, no explanations, no Markdown, NO JSON, and no quotation marks around the answer.
        - Preserve capitalization, spaces, and punctuation EXACTLY as in the TEXT.
        - If there is NO matching passage: respond with <<<NO_MATCH>>>.

        Additional rules:
        - Never provide multiple passages or variations.
        - If multiple passages fit, choose the most precise and shortest exact passage.
        """

def test_golden_pipeline_end_to_end():
  
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    assert pdfs, f"No PDFs found in {INPUT_DIR}"
    
    folder = f"{PROJECT_NAME}"  
    files = [("files", (p.name, p.open("rb"), "application/pdf")) for p in pdfs]
    data = {"folder": folder}
    try:
        r = requests.post(doc("uploadpdfs"), files=files, data=data, timeout=60)
        assert r.status_code in (200, 202), f"uploadpdfs failed: {r.status_code} {r.text}"
        job_id = r.json()["job_id"]

        # wait for docling job to finish
        state = _wait_for_docling_done(job_id, timeout=DOCLING_TIMEOUT)
        assert state == "done", f"Docling job not done, state={state}"

        #list folders available for orchestrator
        r = requests.get(orch("list_html_subfolders"), timeout=ORCH_TIMEOUT)
        assert r.status_code == 200, r.text
        subfolders = r.json()
        assert folder in subfolders, f"folder '{folder}' not listed by orchestrator: {subfolders}"

        # check if token was set
        if not LS_TOKEN:
            pytest.skip("LABEL_STUDIO_LEGACY_TOKEN not set; skipping LS upload step")

        create_payload = {
            "title": PROJECT_NAME,
            "questions": ["What is the patient name?", "What is the diagnosis?"],
            "labels":    ["PATIENT_NAME", "DIAGNOSIS"],
            "token": LS_TOKEN,
        }
        r = requests.post(orch("create_project"), json=create_payload, timeout=ORCH_TIMEOUT)
        assert r.status_code == 200, f"create_project failed: {r.status_code} {r.text}"
        resp = r.json()
        assert resp.get("status") == "success", f"create_project error: {resp}"

        upload_payload = {
            "project_name": PROJECT_NAME,
            "token": LS_TOKEN,
            "html_folder": folder,  # subfolder in data/htmls
        }
        r = requests.post(orch("upload_tasks"), json=upload_payload, timeout=ORCH_TIMEOUT)
        assert r.status_code == 200, f"upload_tasks failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("status") == "success", f"upload_tasks error: {body}"

        prelabel_payload = {
            "project_name": PROJECT_NAME,
            "model": TEST_MODEL, 
            "system_prompt": SYSTEM_PROMPT,
            "qal_file": "questions_and_labels.json",
            "token": LS_TOKEN,
        }

        r = requests.post(orch("prelabel_project"), json=prelabel_payload, timeout=PRELABEL_TIMEOUT)
        assert r.status_code == 200, f"prelabel_project failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("status") == "success", f"prelabel_project error: {body}"


        project_id = _ls_project_id_by_title(PROJECT_NAME, LS_TOKEN)
        export_json = _export_predictions(project_id, LS_TOKEN)
        pred_map = _canon_from_ls_export(export_json)

        if REGEN_BASELINE or not BASELINE_PATH.exists():
            with open(BASELINE_PATH, "w", encoding="utf-8") as f:
                json.dump(pred_map, f, indent=2, ensure_ascii=False)
            print(f"[BASELINE] wrote new baseline to {BASELINE_PATH}")

        # load ground truth if missing skip
        gt_map = {}
        if GROUNDTRUTH_PATH.exists():
            with open(GROUNDTRUTH_PATH, "r", encoding="utf-8") as f:
                gt_map = json.load(f)
        else:
            print(f"[GROUNDTRUTH] missing: {GROUNDTRUTH_PATH} (skipping GT comparison)")

        # load baseline
        with open(BASELINE_PATH, "r", encoding="utf-8") as f:
            baseline_map = json.load(f)

        diff_vs_baseline = _diff(pred_map, baseline_map)
        if diff_vs_baseline:
            msg = "Predictions differ from baseline:\n" + "\n".join(diff_vs_baseline)
            raise AssertionError(msg)
        else:
            print("[BASELINE CHECK] ✅ Predictions match baseline perfectly.")

        if gt_map:
            diff_vs_gt = _diff(pred_map, gt_map)
            if diff_vs_gt:
                msg = "Predictions differ from ground truth:\n" + "\n".join(diff_vs_gt)
                raise AssertionError(msg)
            else:
                print("[GROUND TRUTH CHECK] ✅ Predictions match ground truth perfectly.")
        else:
            print("[GROUND TRUTH CHECK] ⚠️ Skipped (no ground truth file found).")
    finally:
        _cleanup_test_folders(folder)


def _wait_for_docling_done(job_id: str, timeout: int = 180, poll_every: float = 1.5) -> str:
    """Polls /job_status/<job_id> unti state in {'done','error','cancelled'} or Timeout."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = requests.get(doc("job_status", job_id=job_id), timeout=10)
        if r.status_code == 200:
            st = r.json()
            last = st.get("state")
            if last in ("done", "error", "cancelled"):
                return last
        time.sleep(poll_every)
    return last or "unknown"

def _cleanup_test_folders(folder_name: str):
    """Remove generated /pdfs/<folder> and /htmls/<folder> inside the Docling container volume."""
    for base in (PDFS_DIR, HTMLS_DIR, PROJECTS_DIR):
        target = base / folder_name
        try:
            if target.exists():
                shutil.rmtree(target)
                print(f"[CLEANUP] Removed {target}")
        except Exception as e:
            print(f"[WARN] Failed to clean {target}: {e}")

def _ls_project_id_by_title(title: str, token: str) -> int:
    r = requests.get(f"{LABEL_STUDIO_URL}/api/projects", headers={"Authorization": f"Token {token}"}, timeout=60)
    r.raise_for_status()
    items = r.json() if isinstance(r.json(), list) else r.json().get("results") or r.json().get("projects") or []
    for p in items:
        if p.get("title") == title:
            return p["id"]
    raise RuntimeError(f"Project not found: {title}")

def _export_predictions(project_id: int, token: str) -> list[dict]:
    """Fetch tasks with predictions via the project-scoped endpoint."""
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks/"
    params = {"include": "predictions", "page_size": 1000}
    r = requests.get(url, headers={"Authorization": f"Token {token}"}, params=params, timeout=120)
    r.raise_for_status()
    data = r.json()
    # LS may return a list or a dict with 'tasks'/'results'
    if isinstance(data, list):
        return data
    return data.get("tasks") or data.get("results") or []

def _canon_from_ls_export(tasks_json: list[dict]) -> dict[str, dict[str, str]]:
    out = {}
    for t in tasks_json:
        name = (t.get("data") or {}).get("name") or (t.get("data") or {}).get("filename") or f"task-{t.get('id')}"
        pred_blocks = (t.get("predictions") or [])
        # take the last prediction if multiple; adjust if you prefer first
        if not pred_blocks:
            out[name] = {}
            continue
        pred = pred_blocks[-1]
        result = pred.get("result") or []
        label_map = {}
        for r in result:
            val = r.get("value") or {}
            labels = val.get("labels") or []
            text = val.get("text")
            if labels and isinstance(text, str) and text.strip():
                label_map[labels[0]] = text
        out[name] = label_map
    return out

# Simple strict comparisons; customize if you want case-insensitive or whitespace-normalized matching
def _diff(a: dict, b: dict) -> list[str]:
    msgs = []
    keys = sorted(set(a.keys()) | set(b.keys()))
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if va != vb:
            msgs.append(f"{k}: {va} != {vb}")
    return msgs