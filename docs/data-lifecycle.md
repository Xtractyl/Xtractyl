# Data Lifecycle Reference

What gets written to Postgres (and MinIO, where relevant) at each step of each pipeline.
Useful for debugging stuck jobs or verifying data provenance.

---

## Schema Reference

**`projects`**
- `id` (PK)
- `name` (unique, referenced by other tables via name, not id)
- `label_studio_id` (nullable)
- `is_groundtruth` (bool, default false)
- `ls_tasks_uploaded` (bool, default false)
- `questions_and_labels` (JSONB, nullable)
- `labels_hash` (nullable)
- `created_at`, `updated_at`

**`files`**
- `id` (PK)
- `project` (FK → `projects.name`)
- `filename`
- `pdf_key` (nullable — MinIO path for the PDF)
- `html_key` (nullable — MinIO path for the converted HTML)
- `pdf_hash` (nullable)
- `html_hash` (nullable)
- `error` (nullable — per-file conversion error)
- `created_at`, `updated_at`
- unique constraint on `(project, filename)`

**`conversion_jobs`**
- `id` (PK)
- `project` (FK → `projects.name`)
- `status` (`pending` | `converting` | `done` | `failed`)
- `total_files`
- `converted_files` (default 0)
- `error` (nullable — job-level error)
- `created_at`, `updated_at`

**`prelabelling_runs`**
- `id` (PK)
- `project` (FK → `projects.name`)
- `label_studio_id` (nullable)
- `questions_and_labels` (JSONB, nullable)
- `labels_hash` (nullable)
- `ollama_model` (nullable)
- `system_prompt` (nullable)
- `llm_timeout_seconds` (nullable)
- `status` (`pending` | `running` | `done` | `failed`)
- `error` (nullable)
- `created_at`, `updated_at`

**`task_prelabelling_metas`**
- `id` (PK)
- `prelabelling_run_id` (FK → `prelabelling_runs.id`)
- `label_studio_task_id`
- `filename`
- `predictions` (JSONB, nullable)
- `raw_llm_answers` (JSONB, nullable)
- `dom_match_diagnostics` (JSONB, nullable)
- `dom_match_by_label` (JSONB, nullable)
- `task_ms_total`, `task_ms_llm_total`, `task_ms_dom_extract`, `task_ms_dom_match` (float, nullable)
- `n_llm_calls`, `n_timeouts` (nullable)
- `avg_llm_call_ms`, `median_llm_call_ms` (float, nullable)
- `created_at`
- unique constraint on `(prelabelling_run_id, label_studio_task_id)`

**`task_groundtruth_annotations`**
- `id` (PK)
- `project` (FK → `projects.name`)
- `label_studio_task_id`
- `filename`
- `annotations` (JSONB, nullable)
- `created_at`
- unique constraint on `(project, label_studio_task_id)`

**`evaluations`**
- `id` (PK)
- `groundtruth_project` (FK → `projects.name`)
- `comparison_prelabelling_run_id` (FK → `prelabelling_runs.id`)
- `run_at` (nullable)
- `metrics_micro` (JSONB, nullable)
- `metrics_per_label` (JSONB, nullable)
- `filenames_count` (nullable)
- `created_at`

---

## Conversion Pipeline

### 1. When starting a completely new project (new project name, selection of PDFs, conversion to HTMLs etc.)
- No rows for *this* project exist yet in any of the 7 tables: `projects`, `files`, `conversion_jobs`, `prelabelling_runs`, `task_prelabelling_metas`, `task_groundtruth_annotations` and `evaluations`
- MinIO: overall bucket exists (created once, not per project)

### 2. `prepare_conversion` (`POST /conversion/prepare`)
- `projects` row created:
  - `id` — assigned automatically by Postgres (auto-increment)
  - `created_at`, `updated_at` — set automatically by Postgres (`now()`)
  - `name` — set explicitly to `cmd.project`
  - `label_studio_id`, `questions_and_labels`, `labels_hash` — stay `NULL`
  - `is_groundtruth`, `ls_tasks_uploaded` — stay at their default `false`
  - (all of the above except `name` are filled in later by other pipelines, not conversion)
- One `files` row per uploaded filename — only `project`, `filename`, `pdf_key` set; `html_key`, `pdf_hash`, `html_hash`, `error` all null
- `conversion_jobs` row created — `status="pending"`, `total_files=<count>`, `converted_files=0`, `error=null`
- MinIO: nothing written — only presigned upload URLs are generated including a signature and the path for each file according to the pdf_key

### 3a. Upload succeeds
- Frontend `PUT`s the file directly to the presigned URL
- MinIO: PDF bytes now exist at `pdf_key`
- DB: unchanged

### 3b. Upload fails partway
- Handled by `POST /conversion/discard`, called automatically by the frontend on failure — deletes `projects`, `files`, and `conversion_jobs` rows for this project if the job is still `"pending"` **or `"failed"`**
- Fallback: a scheduled cleanup job removes any `conversion_jobs` row still stuck at `"pending"`, `"converting"`, or `"failed"` after a configurable age (`CLEANUP_STALE_AFTER_HOURS`, default 2h), for cases where the abort call itself didn't reach the backend
  - `"pending"` is checked against `created_at` (never made it past prepare — no progress to protect)
  - `"converting"`/`"failed"` are checked against `updated_at` instead, so a job that is still receiving per-file callbacks (see step 5) is never killed mid-flight — only genuinely stuck jobs (e.g. a crashed worker) get cleaned up
- MinIO: both the abort call and the scheduled cleanup also delete any PDF bytes already uploaded under that project's prefix — no orphaned objects remain

### 3c. Orphaned MinIO prefixes with no matching `projects` row
- Separate fallback, runs in the same periodic cleanup loop as 3b: lists all top-level prefixes in the MinIO bucket and compares them against `projects.name`
- Any prefix with no matching row is deleted — this is the actual safety net for the case where `discard_conversion`'s DB deletion committed successfully but the subsequent `storage.delete_prefix` call failed (DB-first ordering means this is the only failure mode possible; the reverse — a MinIO prefix that DB rows still reference — cannot occur)
- Per-prefix error isolation: a failure on one prefix logs and continues, does not abort the rest of the sweep

### 4. `start_conversion` (`POST /conversion/convert`)
- `conversion_jobs.status` → `"converting"`
- Everything else unchanged — no per-file writes happen here, those only start once the worker picks the job up (step 5)


### 5. Worker Conversion (per file)
- On success: `files.html_key`, `files.pdf_hash`, `files.html_hash` are set
- On failure: `files.error` is set instead
- `conversion_jobs.converted_files` += 1 (regardless of per-file success or failure) — done as a single atomic SQL `UPDATE ... SET converted_files = converted_files + 1` (not a Python read-modify-write), so concurrent callbacks can't lose an increment
- `conversion_jobs.updated_at` is bumped in the same statement — this is what the cleanup fallback (step 3b) uses to tell "still making progress" apart from "stuck"
- MinIO: HTML file written to `html_key` (on success only)


### 6. Job reaches a terminal state (`handle_conversion_callback`)
- Fail-fast: as soon as *any* file's callback reports `success=False`, the whole job is immediately set to `"failed"` — the worker is told to stop processing the remaining files for this job, since the project will be discarded anyway
- `conversion_jobs.status` → `"done"` only if every file succeeded; `"failed"` as soon as the first one doesn't
- `conversion_jobs.error` set to `"<filename>: <error>"` for the first file that failed
- On `"failed"`: the frontend automatically fires `POST /conversion/discard` in the background right after showing the error (best effort, failure is swallowed client-side) — so the project name is freed up immediately instead of waiting for the 2h cleanup fallback from step 3b

---

## Create Project Pipeline

### `create_project_main_from_payload` (`POST /create_project`)
- Requires `conversion_jobs.status == "done"` for that project — explicitly checked and rejected with `CONVERSION_NOT_DONE` before any Label Studio call is made. This is a real backend guard (`repo.is_conversion_done`), not just a UI-level filter — calling the endpoint directly for a still-`"converting"` or `"failed"` project is rejected server-side
- Creates a real Label Studio project + attaches the ML backend (external side effects, in this order)
- `projects.label_studio_id` set to the returned Label Studio project ID
- `projects.questions_and_labels` (JSONB) and `projects.labels_hash` set from the submitted questions/labels
- No MinIO writes
- The candidate list shown in the frontend dropdown (`ConvertedProjectSelect`, backed by `GET /list_projects_ready_for_creation`) requires both `label_studio_id IS NULL` **and** `conversion_jobs.status == "done"` — a project still `"converting"` or `"failed"`-but-not-yet-cleaned-up is excluded, so it can't be picked here while its HTML conversion is incomplete


**Resolved finding:** previously, `set_label_studio_id`/`save_questions_and_labels` were silent no-ops if the `projects` row didn't exist — meaning a real Label Studio project (with ML backend attached) could be created while Xtractyl's own DB recorded nothing, with the API still reporting success. Fixed by the existence check above. The frontend also now only lets the project name be chosen from a dropdown of projects that actually exist and don't have a `label_studio_id` yet (`ConvertedProjectSelect`), rather than free text.

---

## Upload Tasks Pipeline

### `upload_tasks_main_from_payload` (`POST /upload_tasks`)
 - Reads `projects.label_studio_id` (must already be set — see Create Project Pipeline above); raises `PROJECT_NOT_FOUND` if unset
 - Raises `TASKS_ALREADY_UPLOADED` if `projects.ls_tasks_uploaded` is already `true` — prevents duplicate task uploads to Label Studio on a repeated call
 - Reads all `files.html_key` for the project (only files that already have a non-null `html_key`, i.e. successfully converted ones); raises `NO_HTML_FILES` if none exist
 - Reads the HTML content for each file directly from MinIO (`storage.get_object`), builds one task per file, uploads them to Label Studio in a single batch call
 - `projects.ls_tasks_uploaded` set to `true` on success
 - No new MinIO writes (read-only against MinIO)
 - Frontend project selection is now a dropdown (`UploadReadyProjectSelect`, backed by `GET /list_projects_ready_for_upload`) instead of free text — structurally limits selection to projects that already have a `label_studio_id` and haven't been uploaded yet
---

## Prelabelling Pipeline

> TODO — not yet reviewed in detail. Touches `prelabelling_runs` (create + status transitions), `task_prelabelling_metas` (per-task write via worker callback). Involves Redis queue state (`status:`, `result:`, `logs:` keys) in addition to Postgres — worth documenting both together since job status lives partly outside Postgres.

---

## Evaluation Pipeline (`evaluate-ai`, `save-as-gt-set`)

> TODO — not yet reviewed in detail. Touches `evaluations` (create), `task_groundtruth_annotations` (create, via Save as GT Set), reads `prelabelling_runs` + `task_prelabelling_metas` + `files`. Known open finding: `get_latest_run` has no status filter (review checklist item #7) — relevant here since it determines which run gets evaluated.

---

## Evaluation Drift

> Read-only — no writes. Reads `evaluations` + `prelabelling_runs` across all groundtruth projects. See `07-evaluation-drift.md` for the read path.