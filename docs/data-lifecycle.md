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
- Handled by `POST /conversion/abort`, called automatically by the frontend on failure — deletes `projects`, `files`, and `conversion_jobs` rows for this project if the job is still `"pending"`
- Fallback: a scheduled cleanup job removes any `conversion_jobs` row still stuck at `"pending"` after a configurable age (`CLEANUP_STALE_AFTER_HOURS`, default 2h), for cases where the abort call itself didn't reach the backend
- MinIO: both the abort call and the scheduled cleanup also delete any PDF bytes already uploaded under that project's prefix — no orphaned objects remain

### 4. `start_conversion` (`POST /conversion/convert`)
- `conversion_jobs.status` → `"converting"`
- Everything else unchanged

### 5. Worker Conversion (per file)
- On success: `files.html_key`, `files.pdf_hash`, `files.html_hash` are set
- On failure: `files.error` is set instead
- `conversion_jobs.converted_files` += 1 (regardless of per-file success or failure)
- MinIO: HTML file written to `html_key` (on success only)

### 6. Last file finishes (`handle_conversion_callback`)
- `conversion_jobs.status` → `"done"` (all files have `html_key`) or `"failed"` (at least one file has no `html_key`)
- `conversion_jobs.error` set to e.g. `"N file(s) failed to convert."` if any failed

---

## Create Project Pipeline

> TODO — not yet reviewed in detail. Touches `projects.label_studio_id`, `projects.questions_and_labels`, `projects.labels_hash` (via `save_questions_and_labels`/`set_label_studio_id`). Known open finding: these writes are silent no-ops if the `projects` row doesn't exist yet (see review checklist item #1/#5) — relevant if Create Project is used before Upload & Convert.

---

## Upload Tasks Pipeline

> TODO — not yet reviewed in detail. Touches `projects.ls_tasks_uploaded`, reads `files.html_key`.

---

## Prelabelling Pipeline

> TODO — not yet reviewed in detail. Touches `prelabelling_runs` (create + status transitions), `task_prelabelling_metas` (per-task write via worker callback). Involves Redis queue state (`status:`, `result:`, `logs:` keys) in addition to Postgres — worth documenting both together since job status lives partly outside Postgres.

---

## Evaluation Pipeline (`evaluate-ai`, `save-as-gt-set`)

> TODO — not yet reviewed in detail. Touches `evaluations` (create), `task_groundtruth_annotations` (create, via Save as GT Set), reads `prelabelling_runs` + `task_prelabelling_metas` + `files`. Known open finding: `get_latest_run` has no status filter (review checklist item #7) — relevant here since it determines which run gets evaluated.

---

## Evaluation Drift

> Read-only — no writes. Reads `evaluations` + `prelabelling_runs` across all groundtruth projects. See `07-evaluation-drift.md` for the read path.