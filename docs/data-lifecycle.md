> This lifecycle has not been perfectly aligned with the current state since the last e2e review, but will be as part of the new e2e review started on 12 Sep 2026.





## Schema Reference

**`projects`**
- `id` (PK)
  - **Set:** at project creation — Conversion Pipeline, step 2 (`prepare_conversion`), automatically by Postgres (auto-increment)
  - **Changed:** never
- `name` (unique, referenced by other tables via name, not id)
  - **Set:** at project creation — Conversion Pipeline, step 2, explicitly to `cmd.project`
  - **Changed:** never
- `label_studio_id` (nullable)
  - **Set:** `NULL` at creation (step 2) — actually populated in Create Project Pipeline, step 1 (`create_project_main_from_payload`), with the ID returned by Label Studio
  - **Changed:** never afterward — a second `/create_project` call currently overwrites it unguarded; a planned guard will prevent this)
- `groundtruth` (Text, `CHECK` constraint on `('none', 'internal', 'external')`, default `'none'`) —
  replaces the old boolean `is_groundtruth`
  - **Set:** `'none'` at creation (step 2)
  - **Changed:** to `'internal'` or `'external'` in Evaluation Pipeline, `save_as_gt_set`
    (`POST /save-as-gt-set`), depending on the caller-supplied `scope` — both scopes share the exact
    same write path and mechanism; they differ only in later matching *breadth*, not in how this
    field itself gets set (see Evaluation Pipeline for the full design)
- `ls_tasks_uploaded` (bool, default false)
  - **Set:** `false` at creation (step 2)
  - **Changed:** to `true` in Upload Tasks Pipeline, `upload_tasks_main_from_payload`, on success
- `questions_and_labels` (JSONB, nullable) — set once at project creation, never edited afterward (no code path updates it again), so it's a stable per-project value for the lifetime of the project
  - **Set:** `NULL` at creation (step 2) — actually populated in Create Project Pipeline, step 1, from the submitted questions/labels
  - **Changed:** never
- `labels_hash` (nullable)
  - **Set:** `NULL` at creation (step 2) — actually populated in Create Project Pipeline, step 1, in the same `save_questions_and_labels` call as `questions_and_labels`
  - **Changed:** never
- `questions_hash` (nullable) — previously undocumented
  - **Set:** in the same `save_questions_and_labels` call as `labels_hash` (Create Project Pipeline, step 1)
  - **Changed:** never
- `document_set_hash` (nullable) — previously undocumented; basis for later evaluation matching (see `sync_missing_evaluations`)
  - **Set:** in Conversion Pipeline, step 6 (`handle_conversion_callback`), once `conversion_jobs.status` transitions to `"done"` (`project_repo.set_document_set_hash`)
  - **Changed:** never
- `created_at`, `updated_at`
  - **Set:** automatically by Postgres at creation (`now()`)
  - **Changed:** `updated_at` automatically on any change to the row

**`files`**
- `id` (PK)
  - **Set:** during `prepare_conversion` (`POST /conversion/prepare`) — automatically by Postgres (auto-increment)
  - **Changed:** never
- `project` (FK → `projects.name`)
  - **Set:** during `prepare_conversion` — one row per uploaded filename
  - **Changed:** never
- `filename`
  - **Set:** during `prepare_conversion`
  - **Changed:** never
- `pdf_key` (nullable — MinIO path for the PDF)
  - **Set:** during `prepare_conversion` (path generated for the presigned upload URL)
  - **Changed:** never
- `html_key` (nullable — MinIO path for the converted HTML)
  - **Set:** `NULL` during `prepare_conversion` — computed by the worker (`convert_file`, Worker
    Conversion, step 5) once `start_conversion` triggers it (built first among the four fields
    computed there), but actually persisted to the database only in `handle_conversion_callback`
    (Orchestrator, step 6), which the worker calls once per file after finishing it — the worker
    itself has no DB access
  - **Changed:** never afterward
- `pdf_hash` (nullable)
  - **Set:** `NULL` during `prepare_conversion` — computed by the worker (`convert_file`, step 5;
    computed second, right after `html_key` is built, before the actual conversion runs), persisted
    the same way as `html_key` above, via `handle_conversion_callback` (step 6)
  - **Changed:** never afterward
- `html_hash` (nullable)
  - **Set:** `NULL` during `prepare_conversion` — computed by the worker (`convert_file`, step 5;
    computed last, after the PDF→HTML conversion itself has run), persisted the same way as
    `html_key` above, via `handle_conversion_callback` (step 6)
  - **Changed:** never afterward
- `error` (nullable — per-file conversion error)
  - **Set:** `NULL` during `prepare_conversion` — computed by the worker (`convert_file`, step 5) on
    failure, persisted the same way, via `handle_conversion_callback` (step 6)
  - **Changed:** never afterward
- `created_at`, `updated_at`
  - **Set:** automatically by Postgres at creation
  - **Changed:** `updated_at` automatically on any change to the row
- unique constraint on `(project, filename)`

**`conversion_jobs`**
- `id` (PK)
  - **Set:** during `prepare_conversion` (`POST /conversion/prepare`) — automatically by Postgres (auto-increment)
  - **Changed:** never
- `project` (FK → `projects.name`)
  - **Set:** during `prepare_conversion`
  - **Changed:** never
- `status` (Text, `CHECK` constraint on `('pending', 'converting', 'done', 'failed', 'cancelled')` —
  `ck_conversion_jobs_status_values`; previously enforced only by an inline comment, no DB-level
  constraint)
  - **Set:** `"pending"` during `prepare_conversion`
  - **Changed:** to `"converting"` when `start_conversion` (`POST /conversion/convert`) triggers Worker Conversion; to `"done"` in `handle_conversion_callback` (step 6) once every file has succeeded; to `"failed"` in `handle_conversion_callback` as soon as the first file's callback reports failure (fail-fast — remaining files are told to stop); to `"cancelled"` via the new cancel endpoint (see Cancel insert after step 6), while `status == "converting"`
- `total_files`
  - **Set:** during `prepare_conversion`, to the count of uploaded files
  - **Changed:** never
- `converted_files` (default 0)
  - **Set:** `0` during `prepare_conversion`
  - **Changed:** incremented by 1 in `handle_conversion_callback` (Orchestrator, step 6) — called once per file by the worker after it finishes, regardless of per-file success or failure — via a single atomic SQL `UPDATE ... SET converted_files = converted_files + 1` (not a Python read-modify-write), so concurrent callbacks can't lose an increment
- `error` (nullable — job-level error)
  - **Set:** `NULL` during `prepare_conversion`
  - **Changed:** set in `handle_conversion_callback` (step 6) to `"<filename>: <error>"` for the first file that failed
- `created_at`, `updated_at`
  - **Set:** automatically by Postgres at creation
  - **Changed:** `updated_at` automatically on any change to the row — this is specifically what the stale-job cleanup fallback (Conversion Pipeline, step 3b) uses to distinguish "still making progress" (bumped alongside every `converted_files` increment) from "genuinely stuck"

**Insert — Row deletion affecting `projects`, `files`, `conversion_jobs`**

These three tables are the only ones whose rows can be deleted outright rather than just updated —
always together, never individually, and always before a `label_studio_id` exists (i.e. before
Create Project Pipeline has run). Two mechanisms can trigger this:

**`discard_conversion` (`POST /conversion/discard`)**
- Called automatically by the frontend on upload failure (step 3b), and also fired automatically
  by the frontend in the background when `conversion_jobs.status` transitions to `"failed"` or
  `"cancelled"` (Conversion Pipeline, step 6, and the Cancel insert below) — best effort, failure
  swallowed client-side
- Deletes the `projects`, `files`, and `conversion_jobs` rows for that project, but only if
  `conversion_jobs.status` is still `"pending"`, `"failed"`, or `"cancelled"` — a job that is
  `"converting"` or already `"done"` is not touched by this endpoint
- Also deletes any PDF bytes already uploaded to MinIO under that project's prefix — no orphaned
  objects remain

**Cleanup container (scheduled, periodic)**
- Fallback for cases where `discard_conversion` itself was never called (e.g. the abort call didn't
  reach the backend) — sweeps `conversion_jobs` rows still stuck at `"pending"`, `"converting"`, or
  `"failed"` after a configurable age (`CLEANUP_STALE_AFTER_HOURS`, default 2h) and deletes the same
  three rows plus any associated MinIO bytes, exactly as `discard_conversion` does
  - `"pending"` jobs are checked against `created_at` (never made it past prepare — no progress to
    protect)
  - `"converting"`/`"failed"` jobs are checked against `updated_at` instead, so a job still
    receiving per-file callbacks (Worker Conversion, step 5) is never killed mid-flight — only
    genuinely stuck jobs (e.g. a crashed worker) get cleaned up
- Separately, in the same periodic run: sweeps orphaned MinIO prefixes with no matching `projects`
  row at all — lists all top-level prefixes in the bucket and compares against `projects.name`;
  any prefix with no matching row is deleted. This is the actual safety net for the case where
  `discard_conversion`'s DB deletion committed but the subsequent `storage.delete_prefix` call
  failed (DB-first ordering means this is the only failure mode possible — a MinIO prefix that DB
  rows still reference cannot occur). Per-prefix error isolation: a failure on one prefix logs and
  continues, does not abort the rest of the sweep

**This same cleanup container additionally sweeps orphaned Label Studio projects**
(`sweep_orphaned_label_studio_projects`) — comparing Label Studio's project list against
`projects.label_studio_id` in the DB and deleting anything unmatched and older than 30 minutes (default value). This is the fallback net for the synchronous compensating deletion in the Create Project Pipeline, for cases where that synchronous
deletion itself fails as well as a guardf against users creating rogue projects directly in label studio. The sweep authenticates against Label Studio using a dedicated,
pre-seeded service account (`LABEL_STUDIO_USER_TOKEN`, set on the `labelstudio` container at first boot via `LABEL_STUDIO_USERNAME`/`LABEL_STUDIO_PASSWORD`/`LABEL_STUDIO_USER_TOKEN`) — distinct from the per-user token that end users paste into the frontend and that is used for all other Label Studio calls. In future one might switch to using the service account authentication for all frontend calls automatically as well instead of passing the token manually.

**`models`**
- `id` (PK)
  - **Set:** at creation — Model Pull Pipeline, step 2 (`reconcile_models`), when a previously unknown digest is found; automatically by Postgres (auto-increment)
  - **Changed:** never
- `tag` — the mutable Ollama tag at pull time (e.g. `gemma3:12b`) — NOT a stable identifier, see `archived_name`
  - **Set:** at creation — Model Pull Pipeline, step 2, from the raw tag returned by Ollama's `/api/tags`
  - **Changed:** never afterward (a new pull of the same digest under a different tag would still resolve to the same `models` row via `digest`, but does not update `tag`)
- `digest` (sha256, unique constraint — the actual stable identity of a model version)
  - **Set:** at creation — Model Pull Pipeline, step 2
  - **Changed:** never
- `archived_name` (unique — `xtractyl-archive/<name>:<digest-short>-<timestamp>`, an independent Ollama model created via `/api/copy` right after pull, sharing blobs with the source but surviving independently if the source tag is later deleted or re-pulled; this is the only name ever sent to Ollama for inference or referenced elsewhere in the app)
  - **Set:** at creation — Model Pull Pipeline, step 2, immediately after the `models` row is created, via `/api/copy`
  - **Changed:** never
- `size_bytes`, `family`, `parameter_size`, `quantization_level` (nullable — from Ollama's `/api/tags` details)
  - **Set:** at creation — Model Pull Pipeline, step 2, from Ollama's `/api/tags` response
  - **Changed:** never
- `ollama_version` (nullable — currently always NULL, `/api/version` not yet wired in)
  - **Set:** `NULL` at creation — Model Pull Pipeline, step 2
  - **Changed:** never (planned: populate once `/api/version` is wired in)
- `pulled_via` (currently always `"user_pull"`)
  - **Set:** `"user_pull"` at creation — Model Pull Pipeline, step 2
  - **Changed:** never
- `status` (`downloaded` | `validated` | `hosted` — only `downloaded` is currently used; `validated`/`hosted` are reserved for the model-hosting phase)
  - **Set:** `"downloaded"` at creation — Model Pull Pipeline, step 2
  - **Changed:** never today (planned: transitions to `validated`/`hosted` once the model-hosting phase, referenced in the README roadmap, ships)
- `first_seen_at` — set at first pull of this digest
  - **Set:** at creation — Model Pull Pipeline, step 2
  - **Changed:** never
- `last_confirmed_at` — updated on every subsequent pull of an already-known digest
  - **Set:** at creation — Model Pull Pipeline, step 2, to the same value as `first_seen_at`
  - **Changed:** in Model Pull Pipeline, step 2, every time `reconcile_models` encounters this digest again on a later pull (digest already known → only this field is updated, no new row, no new Ollama copy)

**`prelabelling_runs`**

- **`UniqueConstraint("project", name="uq_prelabelling_runs_project")`** — at most one row per
  project, enforced at the database level. `enqueue_prelabel_job` catches the resulting
  `IntegrityError` on a second attempt and translates it into a clean `AlreadyExists` API error
  (HTTP 409) rather than letting the raw DB error surface. This closes the gap that previously
  existed between two concurrent requests both passing an application-level check before either
  committed. `enqueue_prelabel_job` additionally checks `get_run_for_project` up front and rejects an existing run in `pending`, `running` or `done` with the same `AlreadyExists` error (step 1).
  A run in `failed`, `incomplete` or `cancelled` is resumed instead (same row, see
  `prelabelling_runs.status`), so in practice the constraint only fires when two first enqueues
  race each other

- `id` (PK)
  - **Set:** at creation — Prelabelling Pipeline, step 1 (`enqueue_prelabel_job`, `POST /prelabel_project`); automatically by Postgres (auto-increment)
  - **Changed:** never
- `project` (FK → `projects.name`)
  - **Set:** at creation — Prelabelling Pipeline, step 1
  - **Changed:** never
- `system_prompt_hash` (nullable) — previously undocumented; unlike `projects.questions_and_labels`, `system_prompt` itself is **not** DB-sourced — it's free text held in the browser's `localStorage` and trusted as submitted, run-scoped only (no project-level canonical value exists)
  - **Set:** at creation — Prelabelling Pipeline, step 1, computed from the client-submitted `system_prompt`
  - **Changed:** never
- `model_id` (FK → `models.id`, NOT nullable — resolved from the `archived_name` string sent by the frontend at enqueue time; `MODEL_NOT_FOUND` is raised if the string isn't a known `archived_name`)
  - **Set:** at creation — Prelabelling Pipeline, step 1, via `get_by_archived_name`
  - **Changed:** never
- `system_prompt` (nullable)
  - **Set:** at creation — Prelabelling Pipeline, step 1, from the client-submitted value
  - **Changed:** never
- `llm_timeout_seconds` (nullable) — currently unused: `create_run` takes no such argument, so it is always `NULL`
  - **Set:** never
  - **Changed:** never
- `status` (`pending` | `running` | `done` | `failed` | `cancelled` | `incomplete`) — enforced by `ck_prelabelling_runs_status_values`
  - **Set:** `"pending"` at creation — Prelabelling Pipeline, step 1
  - **Changed (resume):** from `"failed"`, `"cancelled"` or `"incomplete"` back to `"pending"` in
    Prelabelling Pipeline, step 1 (`run_repo.resume_run`, a conditional UPDATE so concurrent
    resumes can't both succeed), with `error` cleared to `NULL` so a second failure is never
    mistaken for the first one; the run's `failed` rows in `prelabelling_run_tasks` are reset to
    `pending` in the same call, so the derived status below doesn't read a resumed run as finished
  - **Changed (current):** after every `POST /prelabel/task-result`, `run_repo.derive_run_status` (same transaction as the task row, one conditional UPDATE, only for runs in `"pending"` or `"running"`) bumps `updated_at` and derives the status from the run's `prelabelling_run_tasks` rows: `"running"` while any task is still `pending`, `"incomplete"` once no task is `pending` anymore and at least one is `failed`, `"done"` once no task is `pending` or `failed` anymore. `"failed"` is set by the worker's `POST /prelabel/job-failed` (`run_repo.fail_run`, only for a run that is still `"pending"` or `"running"`), which is sent when the worker cannot start or aborts its loop. When the derivation sets `"done"`, the same transaction triggers `sync_missing_evaluations`

  - **Changed (cancel):** `"running"` → `"cancelled"` in `handle_task_result` (`run_repo.apply_cancel`), right after `derive_run_status`, if `cancel_requested` is set. A run the derivation just finished (`"done"`/`"incomplete"`) is not cancelled
  - **Note on `"running"` and `"failed"`:** `"running"` is first set by the first `task-result` of a run, not when the worker picks the job up. A failure before the first task result (e.g. the task list cannot be fetched) therefore goes `"pending"` → `"failed"` directly, skipping `"running"`
  - **Changed (planned):** the stale-run sweep ([TODO 2]) sets `"running"` → `"incomplete"` and `"pending"` → `"failed"` for runs that stopped receiving updates
  - **Note:** evaluation (`sync_missing_evaluations`) only ever triggers on `"done"` — neither `"incomplete"` nor `"cancelled"` trigger it, regardless of how many tasks happened to complete successfully before the run ended
- `error` (nullable)
  - **Set:** `NULL` at creation — Prelabelling Pipeline, step 1
  - **Changed (current):** set by `POST /prelabel/job-failed` together with `"failed"`, as a single value
  - Errors of single tasks are not stored here but in `prelabelling_run_tasks.error`; this column only holds the error of a job that failed as a whole

- `cancel_requested` (bool, NOT NULL, default `false`)
  - **Set:** `false` at creation
  - **Changed:** to `true` by `POST /prelabel/cancel/<job_id>` (`run_repo.request_cancel`, only while the run is `pending` or `running`); back to `false` by `resume_run`. Read by `handle_task_result`, which turns it into `status="cancelled"` and answers the worker with `continue: false`
- **No progress counters.** There are no `processed_tasks`/`total_tasks` columns: progress is derived from the `prelabelling_run_tasks` rows at read time (tasks that are no longer `pending` / all tasks)


- `created_at`, `updated_at`
  - **Set:** automatically by Postgres at creation
  - **Changed:** `updated_at` automatically on any change to the row

**`prelabelling_run_tasks`** — one row per task of a run; the only per-task table (it replaced
`task_prelabelling_metas`, which was dropped). Rows are created at enqueue, updated per task by
`POST /prelabel/task-result`, and `failed` rows are reset to `pending` by `resume_run`. Read by
`derive_run_status`, the status polling (`count_run_tasks`) and `get_successful_run_tasks` (Get
Results, evaluation)
- One row per task of a run, created when a new run is enqueued, so the
  row count is the run's task total and `status` is the task's state.
- `id` (PK), `prelabelling_run_id` (FK → `prelabelling_runs.id`)
- `filename` (NOT NULL) — `basename(files.html_key)`, i.e. the `name` of the Label Studio task,
  not `files.filename` (which is the PDF name)
- `label_studio_task_id` (nullable) — unknown at row creation, set by the first callback for the row
- `status` (`pending` | `success` | `failed`, default `pending`, enforced by
  `ck_prelabelling_run_tasks_status_values`), `error` (Text, nullable)
- Result columns, filled from the ml_backend's `meta` (validated by `TaskResultData`):
  `predictions`, `raw_llm_answers`, `dom_match_diagnostics`, `dom_match_by_label`, `task_ms_*`,
  `n_llm_calls`, `n_timeouts`, `avg_llm_call_ms`, `median_llm_call_ms` — all nullable, empty until
  the task succeeded
- `created_at`, `updated_at` (automatic; `updated_at` changes on every update of the row)
- unique constraints on `(prelabelling_run_id, filename)` and `(prelabelling_run_id, label_studio_task_id)`

**`task_groundtruth_annotations`**

- **No `updated_at` column exists** — every row is written once, in a single batch insert, never
  updated afterward. All fields below share the same "Set" moment.

- `id` (PK)
  - **Set:** at insert — Evaluation Pipeline, `save_as_gt_set` (`POST /save-as-gt-set`), via `project_repo.save_groundtruth_annotations`; automatically by Postgres (auto-increment)
- `project` (FK → `projects.name`)
  - **Set:** at insert — Evaluation Pipeline, `save_as_gt_set`
- `label_studio_task_id`
  - **Set:** at insert — Evaluation Pipeline, `save_as_gt_set`, read live from Label Studio's task list (`_tasks_to_rows(mode="gt")`)
  - **Not currently read back** by the only read path (`get_groundtruth_annotations`, which selects
    just `filename` and `annotations`) or by the evaluation matching itself (`compute_metrics_from_rows`
    keys exclusively on `filename`) — kept regardless, as the traceable link back to the exact Label
    Studio task an annotation came from
- `filename`
  - **Set:** at insert — Evaluation Pipeline, `save_as_gt_set`, read live from Label Studio alongside `label_studio_task_id`
- `annotations` (JSONB, nullable)
  - **Set:** at insert — Evaluation Pipeline, `save_as_gt_set`, the chosen annotation read live from Label Studio for that task
- `created_at`
  - **Set:** automatically by Postgres at insert
- unique constraint on `(project, label_studio_task_id)`

**Guarded against re-running:** `save_as_gt_set` raises `GT_SET_ALREADY_EXISTS` up front if
`projects.groundtruth` is already something other than `'none'` for that project — so this insert
can only ever happen once per project; there is no path that adds or updates rows here a second
time. A second, unrelated guard (`GT_SET_CONTENT_ALREADY_EXISTS`) also rejects the call if another
project with the same `labels_hash` + `document_set_hash` is already a groundtruth set, independent
of the row-level insert itself.

**`evaluations`**

- **No `updated_at` column exists** — every row is written exactly once, in a single insert
  (`eval_repo.save_evaluation`), and the `UniqueConstraint("groundtruth_project",
  "comparison_prelabelling_run_id")` guarantees a given run is never evaluated twice against the same
  groundtruth set — protecting against the two automatic triggers (a run reaching `"done"`, a new GT
  set being saved) racing each other and both firing for the same pair. There is no update path; a
  changed evaluation would be a new row under a different `comparison_prelabelling_run_id`, not a
  revision of an existing one.

- `id` (PK)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run` (the only place an evaluation is ever computed and persisted), called from `sync_missing_evaluations`; automatically by Postgres (auto-increment)
- `groundtruth_project` (FK → `projects.name`)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`
- `comparison_prelabelling_run_id` (FK → `prelabelling_runs.id`)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, passed in explicitly by the caller (deliberately never resolved via a "latest run for this project" lookup here, to avoid the `get_latest_run` ambiguity described elsewhere in this document)
- `run_at` (nullable)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, to `run.updated_at` if set, falling back to `run.created_at` otherwise
- `metrics_micro` (JSONB, nullable)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["micro"]`
- `metrics_per_label` (JSONB, nullable)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["per_label"]`
- `filenames_count` (nullable)
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["filenames_count"]`
- `task_metrics` (JSONB, nullable) — previously undocumented; per-task rows built in `domain/evaluation.py` (`_build_pred_rows`) from `run_repo.get_successful_run_tasks`, i.e. the `success` rows of `prelabelling_run_tasks`
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["task_metrics"]`
- `performance` (JSONB, nullable) — previously undocumented; per-task timing/meta, same source as above
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["performance"]`
- `labels` (JSONB, nullable) — previously undocumented
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["labels"]`
- `created_at`
  - **Set:** automatically by Postgres at insert
- unique constraint on `(groundtruth_project, comparison_prelabelling_run_id)` — with internal
  ground truth now implemented, this comment's original prediction holds structurally without any
  extra guard: `uq_external_groundtruth_labels_documents` allows at most one external GT per
  `(labels_hash, document_set_hash)`, and internal GTs are inherently 1:1 with their own project's
  own run (enforced by `prelabelling_runs`'s own `UNIQUE` constraint on `project`) — so a given run
  can have at most one evaluation of each kind, "1 internal + 1 external", automatically, with no
  additional code needed to enforce it

---

## Conversion Pipeline

### 1. When starting a completely new project (new project name, selection of PDFs, conversion to HTMLs etc.)
- No rows for *this* project exist yet in any of the 7 tables: `projects`, `files`, `conversion_jobs`, `prelabelling_runs`, `prelabelling_run_tasks`, `task_groundtruth_annotations` and `evaluations` 
- MinIO: overall bucket exists (created once, not per project)

### 2. `prepare_conversion` (`POST /conversion/prepare`)
- `projects` row created:
  - `id` — assigned automatically by Postgres (auto-increment)
  - `created_at`, `updated_at` — set automatically by Postgres (`now()`)
  - `name` — set explicitly to `cmd.project`
  - `label_studio_id`, `questions_and_labels`, `labels_hash` — stay `NULL`
  - `groundtruth` — stays at its default `'none'`; `ls_tasks_uploaded` — stays at its default `false`  - (all of the above except `name` are filled in later by other pipelines, not conversion)
- One `files` row per uploaded filename — only `project`, `filename`, `pdf_key` set; `html_key`, `pdf_hash`, `html_hash`, `error` all null
- `conversion_jobs` row created — `status="pending"`, `total_files=<count>`, `converted_files=0`, `error=null`
- MinIO: nothing written — only presigned upload URLs are generated including a signature and the path for each file according to the pdf_key

### 3a. Upload succeeds
- Frontend `PUT`s the file directly to the presigned URL
- MinIO: PDF bytes now exist at `pdf_key`
- DB: unchanged

### 3b. Upload fails partway
- Handled by `POST /conversion/discard`, deletes `projects`, `files`, and `conversion_jobs` rows for this project, allowed while allowed while job is `"pending"`, `"failed"`, or `"cancelled"`. The frontend calls it automatically if:
  - `prepare`/upload/`start` fails before the job is properly under way
  - or later from the polling loop, once the job `"failed"` or has been `"cancelled"`
a failed discard call here is caught and ignored client-side (see the following fallback for this case)
- Fallback: a scheduled cleanup job removes any `conversion_jobs` row still stuck at `"pending"`, `"converting"`, or `"failed"` after a configurable age (`CLEANUP_STALE_AFTER_HOURS`, default 2h), for cases where the abort call itself didn't reach the backend
  - `"pending"` is checked against `created_at` (never made it past prepare — no progress to protect)
  - `"converting"`/`"failed"` are checked against `updated_at` instead, so a job that is still receiving per-file callbacks (see step 5/6) is never killed mid-flight — only genuinely stuck jobs (e.g. a crashed worker) get cleaned up
- MinIO: both the abort call and the scheduled cleanup also delete any PDF bytes already uploaded under that project's prefix — no orphaned objects remain

> **Clarification:** `"failed"` jobs aren't deleted by the cleanup sweep immediately, even though the
> frontend already fires `discard_conversion` automatically on this transition (Conversion Pipeline,
> step 6) — because that automatic frontend call is best-effort, asynchronous, and its failure is
> swallowed client-side. A wait is required specifically to avoid the cleanup sweep racing ahead of
> that call: without one, the periodic sweep could delete the row before the frontend's own discard
> call ever reaches the backend, turning a normal, successful discard into a race instead of a clean
> fallback. In practice this wait is not a fixed 2h for every `"failed"` job — `updated_at` is what's
> checked against `CLEANUP_STALE_AFTER_HOURS`, and the sweep itself runs periodically, so the actual
> wait before a given stale `"failed"` job is caught is somewhere between one sweep interval and the
> full configured threshold, not a guaranteed exact duration.

### 3c. Orphaned MinIO prefixes with no matching `projects` row
- Separate fallback, runs in the same periodic cleanup loop as 3b: lists all top-level prefixes in the MinIO bucket and compares them against `projects.name`
- Any prefix with no matching row is deleted — this is the actual safety net for the case where `discard_conversion`'s DB deletion committed successfully but the subsequent `storage.delete_prefix` call failed (DB-first ordering means this is the only failure mode possible; the reverse — a MinIO prefix that DB rows still reference — cannot occur)
- Per-prefix error isolation: a failure on one prefix logs and continues, does not abort the rest of the sweep

> **Clarification:** the "cannot occur" guarantee holds because *both* deletion paths — not just
> `discard_conversion` — commit the DB deletion before attempting the MinIO deletion:
> `cleanup_stale_conversion_jobs` (the stale-job sweep from 3b) follows the identical DB-first,
> MinIO-second ordering, explicitly commented in the code as "DB state ... now safely persisted ...
> before we touch the irreversible MinIO side". If either path's MinIO deletion fails after its DB
> commit already succeeded, the result is exactly the 3c scenario this sweep exists to catch —
> never the reverse.

### 4. `start_conversion` (`POST /conversion/convert`)
- `conversion_jobs.status` → `"converting"`
- Everything else unchanged — no per-file writes happen here, those only start once the worker picks the job up (step 5/6)

### 5. Worker Conversion (per file)
- `convert_file` builds `html_key`, computes `pdf_hash`, calls Docling, computes `html_hash`, and
  writes the resulting HTML bytes to MinIO at `html_key` — on success only
- No DB writes happen in this step at all — the worker has no direct database access; it reports its
  result (success/failure, `html_key`/`pdf_hash`/`html_hash` or an error string) via a callback to the
  orchestrator, which is where those values actually get persisted (see step 6)

### 6. `handle_conversion_callback` (`POST /conversion/callback`) — runs once per file

> **Clarification:** despite living under "Conversion Pipeline, step 6", this is not a single
> end-of-job callback — it runs once for *every* file the worker finishes, successful or not, and
> returns `{"continue": True/False}` to tell the worker whether to proceed to the next file. It only
> *additionally* transitions the job to a terminal status under specific conditions (see below).

- On failure (`cmd.success=False`):
  - `files.error` is persisted here (`repo.set_file_error`) — computed by the worker in step 5, but
    written to the database only at this point
  - `conversion_jobs.converted_files` incremented (same atomic UPDATE as on success)
  - Fail-fast: if the job isn't already `"failed"`, `conversion_jobs.status` → `"failed"`,
    `conversion_jobs.error` set to `"<filename>: <error>"` for this (first) failing file
  - Returns `continue: False` — the worker is told to stop processing the remaining files for this
    job, since the project will be discarded anyway
- On success (`cmd.success=True`):
  - `files.html_key`, `files.pdf_hash`, `files.html_hash` are persisted here (`repo.set_file_html_key`)
  - `conversion_jobs.converted_files` incremented
  - Guard: if the job's status is already `"failed"` or `"cancelled"` by this point, returns
    `continue: False` without further action. For `"failed"`, this stays unreachable under the
    current strictly sequential, single-worker processing (fail-fast already breaks the per-file
    loop immediately elsewhere) — kept for a future intra-job parallelization where this race could
    actually occur. For `"cancelled"`, the race is real today: cancellation arrives via an
    independent endpoint call (see the Cancel insert below) while a file's conversion may already be
    in flight, so that file's callback can land after the status flip. Its result is still written
    to `files` in that case (`set_file_html_key` runs before this guard) — harmless, since
    `discard_conversion` deletes the row moments later regardless
  - If `converted_files >= total_files`: `conversion_jobs.status` → `"done"`,
    `project_repo.set_document_set_hash(job.project)` is also called (see `projects.document_set_hash`
    in the Schema Reference for what this feeds into), `continue: False`
  - Otherwise: `continue: True`
- `conversion_jobs.updated_at` is bumped in the same statement as the `converted_files` increment —
  this is what the cleanup fallback (step 3b) uses to tell "still making progress" apart from "stuck"


---

## Create Project Pipeline

### `create_project_main_from_payload` (`POST /create_project`)
- Checked in order, both backend-enforced (not just UI-level filtering via the frontend dropdown):
  1. `repo.project_exists(title)` — raises `PROJECT_NOT_FOUND` if the project doesn't exist at all
  2. `repo.is_conversion_done(title)` — raises `CONVERSION_NOT_DONE` if conversion hasn't finished
     successfully; necessary specifically because a project whose conversion failed gets removed
     entirely (see Conversion Pipeline, `discard_conversion`/cleanup), so this guard also implicitly
     covers "project no longer exists because conversion failed"
- Creates a real Label Studio project + attaches the ML backend (external side effects, in this order)
- `projects.label_studio_id` set to the returned Label Studio project ID
- `projects.questions_and_labels` (JSONB) and `projects.labels_hash` set from the submitted questions/labels
- No MinIO writes
- The candidate list shown in the frontend dropdown (`ConvertedProjectSelect`, backed by `GET /list_projects_ready_for_creation`) requires both `label_studio_id IS NULL` **and** `conversion_jobs.status == "done"` — a project still `"converting"` or `"failed"`-but-not-yet-cleaned-up is excluded, so it can't be picked here while its HTML conversion is incomplete

**Resolved finding:** previously, `set_label_studio_id`/`save_questions_and_labels` were silent no-ops if the `projects` row didn't exist — meaning a real Label Studio project (with ML backend attached) could be created while Xtractyl's own DB recorded nothing, with the API still reporting success. Fixed by the `project_exists` check above (step 1 in the ordered check list) — the frontend also now only lets the project name be chosen from a dropdown of projects that actually exist and don't have a `label_studio_id` yet (`ConvertedProjectSelect`), rather than free text.

**Synchronous compensating deletion of the Label Studio project on failure:** if `attach_ml_backend`, 
`set_label_studio_id`, or `save_questions_and_labels` fails *after* the Label
Studio project was already created, `label_studio.delete_project(project_id, token)` is called
before returning an `ExternalServiceError` to the user (with a retry hint) — the DB transaction
itself rolls back on its own (nothing above was committed), but the Label Studio project needed
this explicit compensating call since it lives outside that transaction. If the compensating
deletion itself fails, it's swallowed (the user-facing error is unaffected either way) and the
periodic Label Studio orphan sweep (see the Insert after `conversion_jobs` in the Schema Reference)
is the fallback net.


---

## Upload Tasks Pipeline

`upload_tasks_main_from_payload` (`POST /upload_tasks`)
 - Reads `projects.label_studio_id` (must already be set — see Create Project Pipeline above); raises `PROJECT_NOT_FOUND` if unset
 - Raises `TASKS_ALREADY_UPLOADED` if `projects.ls_tasks_uploaded` is already `true` — prevents duplicate task uploads to Label Studio on a repeated call
 - Reads all `files.html_key` for the project (only files that already have a non-null `html_key`, i.e. successfully converted ones); raises `NO_HTML_FILES` if none exist
 - Reads the HTML content for each file directly from MinIO (`storage.get_object`), builds one task per file, uploads them to Label Studio in a single batch call
 - `projects.ls_tasks_uploaded` set to `true` on success
 - No new MinIO writes (read-only against MinIO)
 - Frontend project selection is now a dropdown (`UploadReadyProjectSelect`, backed by `GET /list_projects_ready_for_upload`) instead of free text — structurally limits selection to projects that already have a `label_studio_id` and haven't been uploaded yet

**On upload failure** — whether a later batch in the `BATCH_SIZE=50` sequence fails, or the
subsequent DB commit (`ls_tasks_uploaded = true`) fails after all batches already succeeded — a
synchronous `label_studio.delete_all_tasks(project_id, token)` call clears every task already
landed in the Label Studio project, rather than tracking and compensating only the specific tasks
from the batches that succeeded, before an `ExternalServiceError` is raised pointing the user to
retry the whole upload. Batching itself (`BATCH_SIZE=50`) stays as-is — this only addresses cleanup
on partial failure, not the batching strategy; Label Studio's bulk-import endpoint has its own
reasons (rate limits, per-call payload size) for not simply switching to one task per call.

**No periodic sweep exists for this case** (unlike the Create Project orphan case above) — a
failed upload is visible to the user in the moment it happens, and manual cleanup directly in Label
Studio remains possible as a fallback if the synchronous `delete_all_tasks` call itself fails.
Longer-term direction (not yet a scoped backlog item): tie Label Studio's live task state more
tightly to Xtractyl's own DB state in general, reducing how much of this category of problem needs
per-pipeline compensating deletions in the first place.

---

## Model Pull Pipeline

### 1. `pull_model` (`POST /ollama/models/pull`)
- Streams the raw Ollama NDJSON pull progress through to the frontend, unchanged
- No DB writes during the stream itself
- After the stream completes (same HTTP request, same generator function): `reconcile_models()`
  runs synchronously before the response closes
- If reconciliation fails, the error propagates to the frontend — the user sees "download
  succeeded, archiving failed" rather than a model that silently never appears in the picker

### 2. `reconcile_models()` (called only from step 1 — no scheduled job, no separate container)
- Calls Ollama `/api/tags`, iterates all locally present models (skips anything already under the
  `xtractyl-archive/` prefix)
- For each tag: looks up `models.digest`
  - Digest already known → only `models.last_confirmed_at` is updated, no new row, no new Ollama copy
  - Digest unknown → `models` row created (`status="downloaded"`), independent Ollama model
    created via `/api/copy` (source: raw tag, destination: `archived_name`)

- **Gap, narrowed by a periodic sweep:** a model pulled outside the app (e.g. directly against the
  Ollama container) isn't archived or documented in `models` until either some pull happens through
  the app, or the periodic cleanup sweep below catches it. `reconcile_models()` itself still only
  runs on a pull through the app, and iterates *every* locally present model on each run, not just
  the one just pulled — so any pull at all through the normal UI/API flow (not necessarily the same
  model that was pulled outside the app) sweeps up and archives every previously untracked model in
  the same pass.

- **Workaround:** trigger any pull through `POST /ollama/models/pull` — pulling the same,
  already-current tag is cheap (Ollama's content-addressed pull mechanism fetches only the manifest,
  not the full model again), so this is a lightweight way to force a reconciliation pass on demand. Adding a 
  frontend button to trigger reconciliation makes the UI more complicated and does not add meaningful
  functionality because: When a user misses a downloaded model she/he will try to re-download it. If it
  was just not reconciled ollama will notice that it already has been downloaded and the backend will directly 
  trigger reconcile_models() without the need of any additional button (and endpoint).
  
**A periodic cleanup sweep** (`sweep_unarchived_ollama_models`, in the same cleanup container as the
other sweeps — see the Insert after `conversion_jobs` in the Schema Reference) catches models that
are (a) not under the `xtractyl-archive/` prefix, (b) whose digest is not in the `models` table, and
(c) older than 24h (a fixed margin, not `CLEANUP_STALE_AFTER_HOURS` — deliberately much larger than
the Label Studio sweep's margin above, since `reconcile_models()` only runs when *some* pull happens
through the app at all, an event with no fixed upper bound on how long it might not occur). This
closes the gap above, and specifically the risk of a model loaded directly against Ollama, bypassing
the app, being selected by curl against `/prelabel_project` (though `enqueue_prelabel_job` already
independently guards against this specific case today by resolving strictly against the `models`
table, never against Ollama directly — see Prelabelling Pipeline). If a user notices a model missing
from the picker within that 24h window, simply re-pulling it triggers `reconcile_models()` again as
a side effect and archives it — no dedicated "reconcile now" UI action exists or is planned, since
this ordinary user reflex already covers the case.

### 3. `list_models` (`GET /ollama/models`)
- Reads directly from Ollama's `/api/tags`, filtered to names starting with `xtractyl-archive/` —
  no DB read here, stays a pure Ollama passthrough
- A model that failed to archive (reconciliation error, see step 1) never appears in this list —
  there's no separate "pending" state surfaced to the picker

### 4. Enqueueing a prelabelling run against an archived model
- `enqueue_prelabel_job` resolves the `archived_name` string sent by the frontend to a `models` row
  (`get_by_archived_name`) purely to obtain `model.id` for the `prelabelling_runs.model_id` FK
- The job payload pushed to the worker queue carries the `archived_name` **string**, never the
  numeric id — Ollama and the worker/ml_backend chain only ever see the archived name, matching
  what `/api/generate` expects

---

## Prelabelling Pipeline

### 1. `enqueue_prelabel_job` (`POST /prelabel_project`)
- Checked in order, all backend-enforced:
  1. `projects.label_studio_id` — `PROJECT_NOT_FOUND` if unset (covers both "project doesn't exist"
     and "project exists but has no `label_studio_id`" with a single ambiguous message; not
     distinguished on purpose, since both cases currently lead to the same remedy for the user)
  2. `projects.questions_and_labels` — `QAL_NOT_FOUND` if unset; should practically never occur in
     practice, since `questions_and_labels` is always set together with `label_studio_id` at Create
     Project time (see Schema Reference), but guarded regardless
  3. `project_repo.tasks_already_uploaded` — `TASKS_NOT_UPLOADED` (409) if `ls_tasks_uploaded` is
     not `true`
  4. `run_repo.get_run_for_project` — `PRELABELLING_RUN_ALREADY_EXISTS` (409) if a run exists with  status `pending`, `running` or `done`
  5. `model_repo.get_by_archived_name(cmd.model)` — `MODEL_NOT_FOUND` if the string isn't a known
     `archived_name`
  6. If `get_run_for_project` found a run in `failed`, `cancelled` or `incomplete`: the run is resumed
     (same `prelabelling_runs` row, status back to `pending`). Model (`model_id`) and system prompt
     (`system_prompt_hash`) must match the run's original values, otherwise `RESUME_CONFIG_MISMATCH`
     (409) — the message carries the original model name and the unchanged prompt text, since the
     error's `meta` never reaches the client. No run → `create_run` as before
  7. `run_repo.get_pending_filenames` — `PENDING_TASKS_NOT_FOUND` (404) if the run has no `pending`
     task rows after it was created or resumed; the request is rolled back and nothing is queued.
     The returned `filename`s travel in the job payload as `task_filenames` (step 2)

> **Resume and the worker:** the worker does not distinguish a fresh run from a resumed one. It
> fetches the open tasks from Label Studio and checks them against `task_filenames` (step 2). Tasks
> that were processed successfully have predictions in Label Studio and rows with `status="success"`,
> so they are neither in the payload nor among the fetched tasks


- `prelabelling_runs` row created — `project`,
  `model_id`, `system_prompt` (+ hash), `status="pending"`. `questions_and_labels`/`labels_hash`/
  `questions_hash` are checked for existence on `projects` (`QAL_NOT_FOUND` if unset) but no longer
  stored on the run itself, they never diverge from `projects.questions_and_labels` (because only
  one run is currently allowed), so consumers
  join against `projects` directly instead (see the Schema Reference's `prelabelling_runs` section).
- One `prelabelling_run_tasks` row per file with an `html_key` is created in the same transaction (`filename = basename(html_key)`, `status="pending"`). Each row is updated by `POST /prelabel/task-result` (step 3); they are the source for the run status, the status polling, Get Results and the evaluation


> **Clarification on why `status` stays `"pending"` here, unlike `conversion_jobs.status` at the
> equivalent point:** for Conversion, all the work that can fail (file uploads, `files` rows) already
> happened *before* the status flip to `"converting"` (back in `prepare_conversion`) — by the time
> `start_conversion` runs, there's nothing left to resolve, only the conversion itself to perform. For
> Prelabelling, it's the other way around: the expensive, failure-prone resolution
> (`get_tasks_without_predictions`, a live Label Studio call) happens
> *after* enqueueing, once the worker picks the job up (step 2). Flipping to `"running"` here, before
> that resolution has even been attempted, would collapse the distinction the `status` design
> deliberately preserves (see `prelabelling_runs.status` in the Schema Reference): a pre-loop
> resolution failure needs to read as `"pending"` → `"failed"` (the loop never started), not
> `"running"` → `"failed"` (which would incorrectly imply it had).

- Redis: the job payload — `job_id`, `project_name`, `label_studio_id`, `model`, `system_prompt`,
  `questions_and_labels` (read from `projects.questions_and_labels` in the same request, never
  submitted by the client), `token` and `task_filenames` — is pushed to the `prelabel_jobs` queue
  (Redis DB 0; separate from `conversion_jobs` in DB 1) through `PrelabelQueueInterface`
  (`RedisPrelabelQueue`; Conversion uses `ConversionQueueInterface` / `RedisConversionQueue`).
  Both Redis queues share the retry logic of `RedisJobQueue`; a push that still fails after the
  retries raises `REDIS_UNAVAILABLE` (HTTP 502) and the request is rolled back

> **Known property — the push happens before the commit:** `enqueue_prelabel_job` pushes the job
> inside the request's transaction, the route commits afterwards. If that commit fails after a
> successful push, the job sits in the queue without its database changes. For a new run there is
> no `prelabelling_runs` row: the worker's first `task-result` is answered with 404
> `RUN_TASK_NOT_FOUND` and fails the job, but by then ml_backend has written that task's
> prediction to Label Studio, so the next start of the project fails with `TASKS_OUT_OF_SYNC`
> (step 2); the fix is to delete that one prediction in Label Studio or to set the project up
> anew. For a resumed run the rows still exist, so the results of the orphaned job are stored,
> while the run status is not changed by them. Accepted deliberately: it needs a failed commit
> right after a successful push, and pushing after the commit would instead leave a `pending` run
> without a job when the push fails, which blocks the project (enqueue guard)

> `GET /list_projects_ready_for_prelabelling` feeds the frontend picker
> (`PrelabellingReadyProjectSelect` on the Start Prelabelling page): projects with
> `ls_tasks_uploaded = true` that have either no `prelabelling_runs` row, or a run whose status is
> not `pending`, `running` or `done` — selecting a run in `failed`/`incomplete`/`cancelled`
> resumes it (step 1, point 6).

### 2. Worker pulls the job, validates the task list, resolves what to process

`resolve_project_id` is no longer called here, `label_studio_id` arrives directly in the job
payload, resolved already by the orchestrator in step 1.
The job payload carries `task_filenames`: the `filename`s of the run's `pending`
`prelabelling_run_tasks` rows at the time of enqueue or resume (`run_repo.get_pending_filenames`).
Before the loop, the worker fetches the open tasks (those without a prediction) from Label Studio
(`get_tasks_without_predictions`) and compares their `name`s with `task_filenames`. The two must
match exactly (same names, each once); otherwise the job fails at once with `TASKS_OUT_OF_SYNC`:
nothing is processed, the message names the differences (shortened), and `POST /prelabel/job-failed`
sets the run to `"failed"` with that message. Postgres is the source of truth. A mismatch means
Label Studio was changed outside of Xtractyl (a task or prediction deleted or added) or an earlier
run died between writing a prediction and reporting it; this is deliberately not repaired. Resuming
such a run fails the same way until the data is consistent again, the practical fix is to set the
project up anew. The tasks the worker processes are still the ones it fetched; `task_filenames`
is only used for this check.
> **What happens today:** `prelabel_project` fetches all tasks without predictions from Label
> Studio, loops over them, calls `/predict` for each and reports every task, successful or not, via
> `send_task_result`.

### 3. Per task: `send_predict` → ml_backend `/predict`
- The worker already holds the task's HTML in memory from the bulk fetch in step 2, so it's passed
  directly in the request body — no second Label Studio round-trip per task
- ml_backend (`run_predict`): extracts the DOM via a freshly-launched headless Chromium
  (Playwright) per task, converts the HTML to plain text via BeautifulSoup for the LLM prompt, asks
  Ollama once per question (`temperature=0, seed=42` for reproducibility), then matches each answer
  back into the DOM (`extract_xpath_matches_from_dom`) to ground it in an actual document location —
  this grounding check is the closest thing the system has to hallucination detection
- A failed question (timeout, connection error, `model_missing` from Ollama) fails the whole task:
  `run_predict` raises `LLM_CALL_FAILED` (HTTP 502) at the first failed question, before any further
  LLM call and before anything is written to Label Studio. An unexpected error in the DOM matching
  raises `DOM_MATCH_FAILED` (HTTP 500). The worker reports every non-200 answer of `/predict` as a
  failed task (`status="failed"`). A matching that runs but does not find an answer is not an error:
  the task stays `success` and the label's entry in `dom_match_by_label` / `dom_match_diagnostics`
  records it

- ml_backend writes to Label Studio: `save_predictions_to_labelstudio` (the actual prediction). This
  will always be necessary, even though the results are also stored in Postgres, because the Label
  Studio GUI is needed to create the ground truth
- After every task the worker calls `send_task_result` (`POST /prelabel/task-result`) — including
  failed tasks (non-200 from `/predict`, task without HTML). The ml_backend's `meta` travels
  unchanged as `result`; the orchestrator's contract (`TaskResultData`) decides which fields are
  stored. The orchestrator updates the matching `prelabelling_run_tasks` row, found by
  `(prelabelling_run_id, filename)` where `filename` is the Label Studio task `name`: `status` is
  `success` or `failed`, `error` is set on failure, result columns only on success. Neither the
  worker nor ml_backend has any direct Postgres access anywhere in the codebase
- This call is not swallowed: a missing row (404 `RUN_TASK_NOT_FOUND`, treated as
  tampering/integrity error, not repaired), a non-200 or a connection error raises in the worker and
  fails the run. After the row is written, the same transaction derives the run status
  (`run_repo.derive_run_status`) and applies a pending cancel (`run_repo.apply_cancel`). The
  response carries `continue`: `false` only if the run is `cancelled`, which makes the worker stop
  its loop (and report `cancelled`)


> **[TODO 1]** Per-task retry and compensation.
> - **Retry with backoff:** `send_predict` and `send_task_result` of each task get their own
>   retry-with-backoff instead of an exception ending the whole run. Today a non-200 `/predict`
>   response is reported as a failed task and the loop continues, while a raised exception (e.g. a
>   dropped connection) aborts the run and sends `job-failed` — two behaviours for the same kind of
>   problem. A `failed` row does not block a retry — `resume_run` resets it to `pending`

> - **Compensating transaction:** if a prediction is successfully written to Label Studio but the
>   corresponding Postgres write (the `task-result` call) fails — even after retry — the Label Studio
>   prediction is deleted again, so the two never permanently disagree. Needs
>   `save_predictions_to_labelstudio` to capture the created prediction's ID (currently discarded)
>   so it can be targeted for deletion

> **Note — `"incomplete"` is never set eagerly:** a failed task does not change
> `prelabelling_runs.status` by itself; `derive_run_status` sets `"incomplete"` only once no task is
> `pending` anymore. This keeps the enqueue guard from treating a run that is still in progress as
> resumable.

### 4. Job completion / cancellation

**Current mechanism (today):**
- The run status is derived from the task rows in `handle_task_result` (step 3). When that sets
  `"done"`, the same transaction triggers `sync_missing_evaluations` (see Evaluation Pipeline) — this
  and `save_as_gt_set` are the only two triggers for this function; it is deliberately not exposed as
  its own route to prevent a user from forcing an evaluation to (re-)compute on demand. An error in
  the evaluation therefore fails the `task-result` call (and with it the run)
- `POST /prelabel/job-failed` (`handle_job_failed`) is the only other writer: the worker calls it when
  it cannot start (project or task-list resolution fails) or aborts its loop (e.g. a rejected
  `task-result`). It sets `"failed"` and the error, only if the run is still `"pending"` or `"running"`
- Cancellation: `POST /prelabel/cancel/:id` only sets `prelabelling_runs.cancel_requested`. The run
  becomes `"cancelled"` with the next `task-result` call (so after the task that is currently
  running), and the response to that call tells the worker to stop (`continue: false`)
- Polling: `GET /prelabel/status/:id` reads the run and counts its task rows; it no longer touches Redis. 
  `state` is the run's status (`pending`, `running`, `done`, `incomplete`, `failed`, `cancelled`), 
  or `cancel_requested` while a `pending`/`running` run has `cancel_requested` set;
  for an id that is not a known run it answers HTTP 200 with `state` `NOT_FOUND`.
  `progress` is the share of task rows that are no longer `pending`. The frontend stops polling on
  any final status and on `NOT_FOUND` (which only clears the stored job id, without a message),
  and picks the message shown at the end from the final status
- Redis is only the job queue (`prelabel_jobs`). The worker's per-task lines go to its normal log 
 (`safe_logger`), not to Redis

> **[TODO 2]** Stale-run sweep in the cleanup container, mirroring Conversion's stale-job sweep (see
> the Insert after `conversion_jobs` in the Schema Reference, `CLEANUP_STALE_AFTER_HOURS`).
>
> Covers runs that stop receiving updates because the worker crashed mid-loop or never picked the
> job up: neither `task-result` nor `job-failed` will ever arrive for them again, and a run in
> `"pending"` or `"running"` blocks its project (enqueue guard, dropdown). `updated_at` of the run
> is the heartbeat; `derive_run_status` bumps it with every task result:
> - `"running"` with a stale `updated_at` → `"incomplete"`, not `"failed"`: the tasks that did
>   finish are valid, and the run can be resumed like any other `"incomplete"` run
> - `"pending"` with a stale `updated_at` → `"failed"`: the worker never started on it. The worker
>   processes jobs one at a time, so the age guard for `"pending"` must be longer than the longest
>   expected wait in the queue
>
> By definition nothing is left executing to perform this check from inside a crashed run, so this
> can only be a periodic sweep.

---

Not planned, and deliberately so — documented here to avoid re-litigating: DOM extraction runs a
fresh headless Chromium per task rather than a reused/injected browser instance. The browser launch
itself is negligible next to LLM call latency, the more expensive part (a `page.evaluate()` round-trip
per DOM element) wouldn't be helped by reusing the browser anyway, and a shared Playwright instance
would need its own concurrency-safety handling. Not worth the complexity for the current, marginal
gain.

---

## Get Results Pipeline

### `build_results_table` (`POST /results/table` — Get Results page)
- Read-only, no writes to any table
- `run_repo.get_run_for_project(cmd.project_name)` resolves the project name to a
  `prelabelling_runs` row; raises `RUN_NOT_FOUND` if none exists; raises `InvalidState("RUN_NOT_DONE")`
  if the resolved run's `status` isn't `"done"`
- Reads the `success` rows of `prelabelling_run_tasks` for that run (`run_repo.get_successful_run_tasks`), flattens `raw_llm_answers` into one column per label
  (`<label>__pred`), returns a table: `task_id`, `filename`, one predicted-answer column per label

- **DB-only, not a Label Studio passthrough** — despite what the route's own OpenAPI contract and
  auth requirement suggest (see the two stale-artifact findings below), this function never calls
  Label Studio at all; it reads exclusively from Postgres via `PrelabellingRunRepository`. This
  appears to be a completed migration (see README, Phase 2: "Migration of filesystem-based state to
  Postgres and MinIO" — marked Completed) whose cleanup was left unfinished at this route
- selectable projects restricted to `status="done"` runs only and a matching `RUN_NOT_DONE` guard added directly in `build_results_table` itself.

**`prelabelling_runs.project` now has a `UNIQUE` constraint** (see the Schema Reference), so
`get_run_for_project` (renamed from `get_latest_run`, used by this pipeline, the Evaluation
Pipeline, and the Evaluation Views) is no longer ambiguous — at most one row can exist per project,
full stop. It still has no explicit status filter and still orders by `created_at DESC` with
`.first()`, but that ordering is now a defensive no-op rather than resolving a real ambiguity, since
there is nothing left to disambiguate between.

---

## Evaluation Pipeline (`evaluate-ai`, `save-as-gt-set`)

**`save_as_gt_set`** (`POST /save-as-gt-set`): reads live from Label Studio (task list + chosen
annotations), writes `task_groundtruth_annotations` and sets `projects.groundtruth` to the caller's
`scope` (`"internal"` or `"external"`). No Label Studio writes happen here at all — only reads — so
unlike Create Project/Upload Tasks there is no orphaned-external-resource risk to compensate for;
the DB writes are already covered by the same commit/rollback-per-request pattern used everywhere
else. Triggers `sync_missing_evaluations` afterward (a new GT set may now retroactively match
existing done runs).

**Internal and external ground truth share the exact same creation mechanism** — `save_as_gt_set`
doesn't branch on `scope` for anything except the final `set_groundtruth` call and one extra guard
(below). Both read the same project's live, chosen Label Studio annotations; neither ever creates a
second project. They differ only in matching *breadth* afterward, in `sync_missing_evaluations` and
in Comparison/Regression/Drift (see below) — never in how the GT itself gets created.

**New guard, `scope="internal"` only:** the project's own run must exist and be `status="done"`
(`RUN_NOT_DONE` otherwise) — there must be finished predictions to review before they can become
ground truth. No equivalent guard exists for external, which is typically annotated from scratch
and often has no run of its own at all.

**`evaluate_run`** (the only place an evaluation is actually computed/persisted): guards against
label-set mismatch (`labels_hash`) and non-identical document sets (`html_hash` set equality,
exact — a 40/41-identical overlap does not qualify) before computing metrics via
`compute_metrics_from_rows` and saving to `evaluations`. No `status == "done"` guard was added inside `evaluate_run` as
`sync_missing_evaluations`, already exclusively iterates `run_repo.list_done_runs()`.

**`sync_missing_evaluations`**: the only two triggers are a run reaching `"done"` and a new GT set
being saved; deliberately not exposed as its own route (see Prelabelling Pipeline). Matches purely
on `(labels_hash, document_set_hash)` — `questions_hash`, `system_prompt`, and the model used play no
role in *whether* an evaluation gets created, only in how Comparison/Regression/Drift later group the
results that exist.

> **Internal-scope exclusion in the matching loop:** one added condition —
> `if gt.groundtruth == "internal" and gt.name != run.project: continue` — inside the existing
> double loop (done runs × GT projects sharing a `(labels_hash, document_set_hash)` key). External
> matching is completely unaffected (the condition is always `False` for it). Internal GTs are
> restricted to matching only their own originating project's own run — never scanned broadly like
> external. This is the *only* code change `sync_missing_evaluations` needed for the whole feature.

`get_run_for_project` (the repository method backing this pipeline, plus `build_results_table`) has
no explicit status filter, but this is no longer ambiguous — see the Get Results Pipeline section
and the `prelabelling_runs` Schema Reference entry for why.

**`compute_metrics_from_rows`'s TN/FP classification requires the literal `<<<NO_MATCH>>>`
sentinel for a TN.** A falsy-but-not-sentinel prediction (empty string, `None`, missing key) is
classified as FP instead — the model failed to follow the required "signal no-match via the
sentinel" convention, which is itself a real, countable error (`orchestrator/domain/utils/calculate_metrics.py`).
 

**Internal ground truth sets — implemented.** See the guard, matching-loop exclusion above for the
Evaluation Pipeline's own share of the work; see Evaluation Drift, Regression, Comparison below for
how the three views consume both scopes.

---

## Evaluation Drift, Regression, Comparison

Read-only across all three views — no writes. All accept an optional `scope` (`"internal"` |
`"external"`, default `"external"`) — driven by one shared, page-level toggle in the frontend
(`EvaluationDriftView.jsx`), not a per-tab control. Internal and external are essentially never
wanted simultaneously in practice (internal exists specifically *because* no external standard was
available), so the three views show one scope at a time rather than merging both into one table.

**All three views are now fully project-attribute-driven.** `resolve_family_for_project` and
`EvaluationRepository.find_evaluation_for_run` had no remaining callers and have been removed. The old model (pick a project → resolve to *one* canonical GT → show its
evaluations) only ever worked because external guaranteed at most one GT per
`(labels_hash, document_set_hash)` — there was never a choice to make. Internal breaks that
assumption: many different projects can coincidentally share a labels/document combination, each
with its own valid, independent internal GT. All three views derive their filter criteria directly
from the *picked project's own* attributes instead, regardless of whether that project is itself a
GT or an ordinary evaluated project:

- **Comparison** (`get_comparison_view`): reads the picked project's own `labels_hash` and
  `document_set_hash` directly (no run lookup needed — both live on `projects` itself), then calls
  `find_internal_evaluations_by_labels_and_document_set` or
  `find_external_evaluations_by_labels_and_document_set` depending on `scope`. External needs no
  separate GT-name filter at all — `uq_external_groundtruth_labels_documents` already guarantees at
  most one external GT can ever match, so the query naturally returns the right (single) GT's
  evaluations without resolving which one it is first.
- **Regression** (`get_regression_view`): reads `labels_hash`/`questions_hash` from the picked
  project itself (`projects.labels_hash`/`.questions_hash` — `prelabelling_runs` no longer stores
  its own copy of these — see the `prelabelling_runs` entry in the Schema Reference)
  and `model_digest`/`system_prompt_hash` from the project's own run
  (`run_repo.get_run_for_project(project_name)`), then calls `find_internal_evaluations_by_configuration`
  
  or `find_external_evaluations_by_configuration`. Those two methods filter only on
  labels/questions/model/prompt, not document set (Drift, the other caller, deliberately needs
  matches across *different* document sets) — so `get_regression_view` applies its own post-filter
  restricting results to the picked project's own `document_set_hash`, restoring "same documents,
  only time varies" for both scopes uniformly. Requires at least 2 matching evaluations to show anything.
  For `scope="internal"`, this means multiple different internal-GT projects can legitimately
  appear together — but only when they happen to share genuinely identical documents, not merely
  the same configuration; a coincidence, not the common case. The response carries no single
  top-level `groundtruth_project` field (no longer meaningful once multiple different internal GTs
  could in principle appear) — each entry carries its own `groundtruth_project`, same as it always
  did per-row.
- **Drift** (`get_drift_view`): same configuration, but *different* document sets with provably zero
  overlap between them (exact set intersection on `html_hash`, not just a different aggregate
  `document_set_hash` — a 40/41-identical overlap is correctly excluded).
  1. Reads the same configuration as Regression (project's own `labels_hash`/`questions_hash`,
     run's own `model_digest`/`system_prompt_hash`) and pulls all matching evaluations via the same
     `find_internal_evaluations_by_configuration` / `find_external_evaluations_by_configuration`
     pair, scoped by `scope`.
  2. **Dedups by `document_set_hash`, keeping the newest evaluation per unique document set** — a
     deliberate choice, not an accident: `matching` is ordered ascending by `run_at`, and the loop
     uses a plain `by_docset[gt.document_set_hash] = e` assignment (not `setdefault`), so each later
     (newer) evaluation for an already-seen document set overwrites the earlier one, leaving the
     most recent evaluation as the representative once the loop finishes. The document set's own
     hash is looked up via `e.groundtruth_project`, not via the comparison run's own project — not
     because the two would differ (`evaluate_run`'s `HTML_HASH_MISMATCH` guard, see Evaluation
     Pipeline, guarantees the GT's document set and the evaluated run's own project's document set
     are always identical whenever an Evaluation exists at all), but because it's the cheaper
     lookup path: one `project_repo.get_project()` call, versus a
     `run_repo.get_run()` → `project_repo.get_project()` detour via the comparison run if looked up
     the other way.
  3. Checks the picked project's own `document_set_hash` is among the deduplicated candidates, and
     that there are at least 2 unique document sets total — otherwise returns empty; no point
     starting the expensive pairwise overlap check otherwise.
  4. Only the deduplicated, unique document sets go through the pairwise overlap check
     (`get_html_hashes_for_project` per candidate). Since "no overlap" isn't a transitive relation,
     there is no single natural grouping once more than two compatible document sets exist for a
     configuration — `_find_best_drift_chain` finds the largest overlap-free chain containing the
     picked project's own document set via brute-force `itertools.combinations`, deliberately
     simple since the candidate set is already pre-filtered to one configuration, one scope, and
     already deduplicated by document set.

**Four repository methods** back Comparison and Regression above:
`find_internal_evaluations_by_labels_and_document_set`,
`find_internal_evaluations_by_configuration`,
`find_external_evaluations_by_labels_and_document_set`,
`find_external_evaluations_by_configuration`. Drift reuses the `*_by_configuration` pair (shared
with Regression) rather than needing its own — the internal/external split already happens at that
level; Drift's only additional step beyond Regression is the document-set dedup and overlap-chain
search described above.
