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
  - **Changed:** never afterward (see Open Findings — a second `/create_project` call currently overwrites it unguarded; a planned guard will prevent this)
- `is_groundtruth` (bool, default false) — **planned:** becomes categorical (`no`/`internal`/`external`) once internal ground truth sets ship; naming not yet decided
  - **Set:** `false` at creation (step 2)
  - **Changed:** to `true` in Evaluation Pipeline, `save_as_gt_set` (`POST /save-as-gt-set`)
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
- `status` (`pending` | `converting` | `done` | `failed` | `cancelled`)
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

**⚠️ Insert — Row deletion affecting `projects`, `files`, `conversion_jobs`**

These three tables are the only ones whose rows can be deleted outright rather than just updated —
always together, never individually, and always before a `label_studio_id` exists (i.e. before
Create Project Pipeline has run). Two mechanisms can trigger this:

**`discard_conversion` (`POST /conversion/discard`)**
- Called automatically by the frontend on upload failure (step 3b), and also fired automatically
  by the frontend in the background when `conversion_jobs.status` transitions to `"failed"`
  (Conversion Pipeline, step 6) — best effort, failure swallowed client-side
- Deletes the `projects`, `files`, and `conversion_jobs` rows for that project, but only if
  `conversion_jobs.status` is still `"pending"` or `"failed"` — a job that is `"converting"` or
  already `"done"` is not touched by this endpoint
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

> **[BACKLOG #13]** Planned: this same cleanup container additionally sweeps orphaned Label Studio
> projects — comparing Label Studio's own project list against `projects.label_studio_id`, deleting
> anything unmatched and older than a configurable age guard (to avoid racing a project that was
> created moments ago and hasn't been persisted yet). Fallback net for [BACKLOG #12] (synchronous
> deletion) in case that synchronous deletion itself fails. See Create Project Pipeline for the
> synchronous half of this mechanism.

*(End of insert.)*

**`models`**
- `id` (PK)
  - **Set:** at creation — Model Pull Pipeline, step 2 (`reconcile_models`), when a previously unknown digest is found; automatically by Postgres (auto-increment)
  - **Changed:** never
- `tag` — the mutable Ollama tag at pull time (e.g. `gemma3:12b`) — NOT a stable identifier, see `archived_name`
  - **Set:** at creation — Model Pull Pipeline, step 2, from the raw tag returned by Ollama's `/api/tags`
  - **Changed:** never afterward (a new pull of the same digest under a different tag would still resolve to the same `models` row via `digest`, but does not update `tag` — see Open Findings if this needs clarifying)
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

- **Missing constraint, planned:** no `UNIQUE` constraint exists today on `project` — `PrelabellingRun`
  has no `__table_args__` at all, so nothing at the database level currently prevents multiple rows
  per project. This is inconsistent with the intended semantics already implied by Planned Changes
  point 5: a `pending`/`running`/`done` run blocks a new one from being created, and a `failed` run is
  *resumed* (the existing row reused, not a new one inserted) — meaning the application's own design
  already assumes at most one row per project, ever. The guard planned in point 5 is
  application-level only (a check inside `enqueue_prelabel_job`); a `UNIQUE` constraint on `project`
  would close the same gap at the database level, immune to a race between two concurrent requests
  both passing the Python-level check before either commits. Proposed: add
  `UniqueConstraint("project", name="uq_prelabelling_runs_project")`, with `enqueue_prelabel_job`
  catching the resulting `IntegrityError` and translating it into the same clean API error the
  application-level guard would have produced

- `id` (PK)
  - **Set:** at creation — Prelabelling Pipeline, step 1 (`enqueue_prelabel_job`, `POST /prelabel_project`); automatically by Postgres (auto-increment)
  - **Changed:** never
- `project` (FK → `projects.name`)
  - **Set:** at creation — Prelabelling Pipeline, step 1
  - **Changed:** never
- `label_studio_id` (nullable)
  - **Set:** at creation — Prelabelling Pipeline, step 1, read fresh from `projects.label_studio_id`
  - **Changed:** never
  - **Dead redundancy, planned for removal:** written at creation but never read again anywhere in
    the codebase — `projects.label_studio_id` is the actual source of truth, and every consumer
    (Upload Tasks, the Prelabelling worker via its own `resolve_project_id` call) either reads
    `projects` directly or re-resolves it independently rather than reading this column. Unlike
    `questions_and_labels`/`labels_hash`/`questions_hash` below, this isn't in Planned Changes point 7
    today — added here as a newly identified candidate for the same cleanup
- `questions_and_labels` (JSONB, nullable) — always taken from `projects.questions_and_labels` at enqueue time (`project_repo.get_questions_and_labels`), **never** from the client request, even though the request contract currently also carries a `questions_and_labels` field (that field is presently unused dead weight, planned for removal)
  - **Set:** at creation — Prelabelling Pipeline, step 1, from `projects.questions_and_labels`, not from the client
  - **Changed:** never (planned: this column removed entirely — see Planned Changes point 7; queries move to joining against `projects` instead, since the value can never diverge from it)
- `labels_hash` (nullable)
  - **Set:** at creation — Prelabelling Pipeline, step 1, alongside `questions_and_labels`
  - **Changed:** never (planned: removed — see Planned Changes point 7)
- `questions_hash` (nullable) — previously undocumented
  - **Set:** at creation — Prelabelling Pipeline, step 1, alongside `labels_hash`
  - **Changed:** never (planned: removed — see Planned Changes point 7)
- `system_prompt_hash` (nullable) — previously undocumented; unlike `questions_and_labels`, `system_prompt` itself is **not** DB-sourced — it's free text held in the browser's `localStorage` and trusted as submitted, run-scoped only (no project-level canonical value exists)
  - **Set:** at creation — Prelabelling Pipeline, step 1, computed from the client-submitted `system_prompt`
  - **Changed:** never
- `model_id` (FK → `models.id`, NOT nullable — resolved from the `archived_name` string sent by the frontend at enqueue time; `MODEL_NOT_FOUND` is raised if the string isn't a known `archived_name`)
  - **Set:** at creation — Prelabelling Pipeline, step 1, via `get_by_archived_name`
  - **Changed:** never
- `system_prompt` (nullable)
  - **Set:** at creation — Prelabelling Pipeline, step 1, from the client-submitted value
  - **Changed:** never
- `llm_timeout_seconds` (nullable)
  - **Set:** at creation — Prelabelling Pipeline, step 1
  - **Changed:** never
- `status` (`pending` | `running` | `done` | `failed` | `cancelled` | `incomplete`) — no DB-level CHECK constraint enforcing this set
  - **Set:** `"pending"` at creation — Prelabelling Pipeline, step 1
  - **Changed (current):** today, no other transition is written to this column at all — `"running"` only ever exists in the Redis status hash, and the terminal states are set by whatever the worker's end-of-job callback happens to report; this column effectively only ever shows `"pending"` in practice
  - **Changed (planned):** transitions to `"running"` together with `total_tasks` being set for the first time, on the first successful progress callback of the run (Planned Changes point 4) — i.e. only once project/task-list resolution (Prelabelling Pipeline, step 2) has already succeeded; a pre-loop failure in that resolution step therefore goes `"pending"` → `"failed"` directly, skipping `"running"` entirely. From `"running"`: to `"done"` once `processed_tasks >= total_tasks` and every task succeeded; to `"incomplete"` under the same completion condition if at least one task's row in `task_prelabelling_metas` ended as `status="failed"` after retries were exhausted (loop continues past individual task failures rather than aborting — see Planned Changes point 4); to `"cancelled"` if `cancel_requested` was set and the worker's `should_stop` check (derived from it) ended the loop early; to `"failed"` only for a genuine hard abort of the whole loop (an exception class not covered by the planned per-task retry-with-backoff)
  - **Note:** evaluation (`sync_missing_evaluations`) only ever triggers on `"done"` — neither `"incomplete"` nor `"cancelled"` trigger it, regardless of how many tasks happened to complete successfully before the run ended
- `error` (nullable)
  - **Set:** `NULL` at creation — Prelabelling Pipeline, step 1
  - **Changed (current):** set by the worker's end-of-job callback on `"failed"`, as a single value
  - **Changed (planned):** type changes from a single error string to a **JSONB array** of `{filename, error}` entries — chosen over text-concatenation (the `conversion_jobs.error` style) because that style was built for a single-failure, fail-fast case, whereas here multiple tasks can fail independently while the loop continues; JSONB keeps this machine-readable without needing to parse a delimited string, and matches the JSONB type already used elsewhere in this table's row-level sibling (`task_prelabelling_metas.predictions`, `.raw_llm_answers`). Appended to (not overwritten) via `send_task_progress` (Planned Changes point 4) each time a task ends with `status="failed"` after its own retry-with-backoff is exhausted; on a hard pre-loop or mid-loop abort (`"failed"` status), holds a single-entry array for that failure instead
- **planned:** `processed_tasks`, `total_tasks`, `cancel_requested` (bool) — replacing the Redis-based job status/progress/cancel tracking
  - **Set (once implemented):** `total_tasks` set once, from the worker's own task-list length, on the first progress call of a given run (see `status` above — this is the same write that also flips status to `"running"`)
  - **Changed (once implemented):** `processed_tasks` incremented atomically per task, regardless of that task's success/failure, via the renamed per-task callback (`send_task_progress` / `/prelabel/progress`); `cancel_requested` set via the new cancel endpoint, read by the worker via the same progress callback's response (`should_stop`)
- `created_at`, `updated_at`
  - **Set:** automatically by Postgres at creation
  - **Changed:** `updated_at` automatically on any change to the row

**`task_prelabelling_metas`**

- **No `updated_at` column exists** — every row is written exactly once, in a single insert, never
  updated afterward. All fields below share the same "Set" moment; there is no "Changed" for any of
  them under current behavior.

- `id` (PK)
  - **Set:** at insert — Prelabelling Pipeline, step 3, via `send_task_meta` (`POST /prelabel/task-meta`), the orchestrator call the worker makes after forwarding a completed task's `meta` from ml_backend; automatically by Postgres (auto-increment)
- `prelabelling_run_id` (FK → `prelabelling_runs.id`)
  - **Set:** at insert — Prelabelling Pipeline, step 3
- `label_studio_task_id`
  - **Set:** at insert — Prelabelling Pipeline, step 3
- `filename`
  - **Set:** at insert — Prelabelling Pipeline, step 3
  - **Planned:** validated against `files.filename` before insert (Planned Changes point 1) — a task without a matching filename is skipped with a warning instead of being written here with `filename=""` or an unverified name, as happens today
- `predictions` (JSONB, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `run_predict` output
- `raw_llm_answers` (JSONB, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `run_predict` output
- `dom_match_diagnostics` (JSONB, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `extract_xpath_matches_from_dom` output
- `dom_match_by_label` (JSONB, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `extract_xpath_matches_from_dom` output
- `task_ms_total`, `task_ms_llm_total`, `task_ms_dom_extract`, `task_ms_dom_match` (float, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `PerfCollector` output
- `n_llm_calls`, `n_timeouts` (nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `PerfCollector` output
- `avg_llm_call_ms`, `median_llm_call_ms` (float, nullable)
  - **Set:** at insert — Prelabelling Pipeline, step 3, from ml_backend's `PerfCollector` output
- **planned:** `status` (`success` | `failed`), `error` (Text, nullable) — the table currently has no
  explicit success/failure field at all; every row implicitly represents a successful task today
  - **Set (once implemented):** at insert, alongside every other field — Prelabelling Pipeline, step 3; `status="success"` for a normal completion, `status="failed"` (with `error` populated) for a task whose DOM extraction/matching crashed or whose retry-with-backoff (Planned Changes point 4) was exhausted; a timeout on any single question fails the whole task (nothing written to Label Studio in that case)
  - **Note:** a `failed` row is kept for visibility/debugging but does **not** block a future retry from reprocessing that task — the retry/resume filter (Planned Changes point 5) checks specifically for `status="success"` under a given run's id, not mere row existence
- `created_at`
  - **Set:** automatically by Postgres at insert
- unique constraint on `(prelabelling_run_id, label_studio_task_id)`

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
`projects.is_groundtruth` is already `true` for that project — so this insert can only ever happen
once per project; there is no path that adds or updates rows here a second time. A second, unrelated
guard (`GT_SET_CONTENT_ALREADY_EXISTS`) also rejects the call if another project with the same
`labels_hash` + `document_set_hash` is already a groundtruth set, independent of the row-level
insert itself.

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
- `task_metrics` (JSONB, nullable) — previously undocumented; per-task rows built from `run_repo.build_pred_rows_for_run`, ultimately sourced from `task_prelabelling_metas`
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["task_metrics"]`
- `performance` (JSONB, nullable) — previously undocumented; per-task timing/meta, same source as above
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["performance"]`
- `labels` (JSONB, nullable) — previously undocumented
  - **Set:** at insert — Evaluation Pipeline, `evaluate_run`, from `compute_metrics_from_rows(...)["labels"]`
- `created_at`
  - **Set:** automatically by Postgres at insert
- unique constraint on `(groundtruth_project, comparison_prelabelling_run_id)` — the constraint's own
  in-code comment already anticipates internal ground truth: *"running against different groundtruth
  sets will only be allowed for 1 internal groundtruth and 1 external groundtruth"* — this is
  schema-level groundwork laid before the feature itself was scoped

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

> **Planned fix (new, not yet in the numbered backlog):** reverse the order in `start_conversion` —
> currently `queue.push_conversion_job(...)` runs *before* `repo.set_conversion_job_status(job.id,
> "converting")`, meaning a fast worker could in principle begin processing the job while
> `conversion_jobs.status` in the DB still reads `"pending"`. This breaks the DB-first ordering
> otherwise held consistently elsewhere (see 3b/3c) — not currently causing a known bug, since the
> worker doesn't consult this status column before acting on a queued payload, but inconsistent with
> the pattern and worth closing for the same reason the other DB-first guarantees exist. Fix: set
> `status = "converting"` and commit *before* pushing the job onto the queue.

### 5. Worker Conversion (per file)
- `convert_file` builds `html_key`, computes `pdf_hash`, calls Docling, computes `html_hash`, and
  writes the resulting HTML bytes to MinIO at `html_key` — on success only
- No DB writes happen in this step at all — the worker has no direct database access; it reports its
  result (success/failure, `html_key`/`pdf_hash`/`html_hash` or an error string) via a callback to the
  orchestrator, which is where those values actually get persisted (see step 6)

> **[BACKLOG #18]** Planned: eliminate the double PDF download — the worker currently downloads the
> PDF twice per file: once itself (`minio.get_object`, needed to compute `pdf_hash`) and once more
> independently by Docling (via a presigned URL the worker also generates). Since the worker already
> holds the full bytes in memory for hashing, it's planned to hand them to Docling directly instead
> of a second, separate download.

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
  - Guard: if the job's status is already `"failed"` by this point, returns `continue: False` without
    further action — unreachable under the current strictly sequential, single-worker processing
    (fail-fast already breaks the per-file loop immediately elsewhere), kept as a guard for a future
    intra-job parallelization where this race could actually occur
  - If `converted_files >= total_files`: `conversion_jobs.status` → `"done"`,
    `project_repo.set_document_set_hash(job.project)` is also called (see `projects.document_set_hash`
    in the Schema Reference for what this feeds into), `continue: False`
  - Otherwise: `continue: True`
- `conversion_jobs.updated_at` is bumped in the same statement as the `converted_files` increment —
  this is what the cleanup fallback (step 3b) uses to tell "still making progress" apart from "stuck"

> **⚠️ Insert — Cancel mechanism for `"converting"` jobs [BACKLOG #17, revised]**
>
> A separate, active-interruption mechanism — deliberately not folded into `discard_conversion`, which
> only ever handles `pending`/`failed`: a reactive cleanup of jobs that never got going or already
> failed on their own, not a user-initiated interruption of one currently running.
>
> **1. `POST /conversion/cancel/:job_id` (new endpoint)**
> - Only valid while `conversion_jobs.status == "converting"`
> - Sets `status = "cancelled"`, commits, returns immediately — deletes nothing itself
>
> **2. The next per-file callback (`handle_conversion_callback`, step 6) is the actual deletion trigger**
> - Checks `status == "cancelled"` before processing the incoming per-file result
> - If cancelled: the just-reported file's result is discarded (not written to `files`), `continue:
>   False` is returned to the worker, and this same callback invocation performs the deletion
>   (`repo.delete_project_cascade` + `storage.delete_prefix`) — same as `discard_conversion` does for
>   `pending`/`failed`
> - This two-step design (signal now, delete only on the worker's own next callback) is what avoids a
>   race between deletion and an in-flight write — the same reason `discard_conversion` already
>   refuses to touch a `"converting"` job today. The worker never performs the deletion itself; the
>   orchestrator does, triggered by the callback the worker was always going to send anyway
>
> **Frontend naming:** button labeled "Cancel and Delete Project", endpoint named to match (e.g.
> `cancel_and_delete_conversion`) — this is always one-way; a cancelled job cannot be revived
>
> **Cleanup container:** `"cancelled"` added to the stale-sweep's status filter alongside `"failed"`,
> checked against `updated_at` with the same `CLEANUP_STALE_AFTER_HOURS` threshold — fallback for the
> case where the worker never sends that triggering callback at all (e.g. it crashed before noticing
> the cancellation). Same rationale as the `"failed"` case at step 3b: the wait avoids the sweep racing
> ahead of the callback-driven deletion.

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

**Open findings, planned fixes:**

> **[BACKLOG #12]** Planned: synchronous compensating deletion of the Label Studio project if
> `attach_ml_backend`, `set_label_studio_id`, or `save_questions_and_labels` fails *after* the Label
> Studio project was already created — the DB transaction rolls back (nothing was committed), but the
> Label Studio project itself is never deleted today, leaving an orphan. Requires a new
> `delete_project` capability in the Label Studio client, which doesn't exist yet; the user sees a
> clear error with a retry hint.

> **[BACKLOG #13]** As a fallback net for cases where the synchronous deletion above itself fails: a
> periodic sweep (the same cleanup container already covering the MinIO-orphan and stale-job sweeps —
> see the Insert after `conversion_jobs` in the Schema Reference) comparing Label Studio's own project
> list against `projects.label_studio_id`, deleting anything unmatched and older than a configurable
> age guard (to avoid racing a project that was created moments ago and hasn't been persisted yet).

> **[BACKLOG #9]** Planned: guard against a second `/create_project` call when `label_studio_id` is
> already set (`PROJECT_ALREADY_HAS_LABEL_STUDIO_ID`) — today, `create_project_main_from_payload`
> never checks this before proceeding; calling the endpoint a second time for the same project
> (bypassing the frontend dropdown) silently creates a *second* Label Studio project and overwrites
> the stored `label_studio_id`, orphaning the first one in a way the [BACKLOG #13] sweep wouldn't
> catch either (the row *does* have a `label_studio_id`, just the wrong one).

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

> **[BACKLOG #14, revised]** Planned: on upload failure — whether a later batch in the `BATCH_SIZE=50`
> sequence fails, or the subsequent DB commit (`ls_tasks_uploaded = true`) fails after all batches
> already succeeded — a synchronous `delete_all_tasks(project_id, token)` call clears every task
> already landed in the Label Studio project, rather than tracking and compensating only the specific
> tasks from the batches that succeeded. Batching itself (`BATCH_SIZE=50`) stays as-is — the failure
> mode being fixed is the lack of cleanup on partial failure, not the batching strategy, and
> Label Studio's bulk-import endpoint has its own reasons (rate limits, per-call payload size) for
> not simply switching to one task per call. The error message returned to the user explicitly points
> to retrying the upload.
>
> **No periodic sweep planned here** (unlike the Create Project orphan case, [BACKLOG #13]) — a
> failed upload is visible to the user in the moment it happens, and manual cleanup directly in Label
> Studio remains possible as a fallback if the synchronous `delete_all_tasks` call itself fails.
> Longer-term direction (not yet a scoped backlog item): tie Label Studio's live task state more
> tightly to Xtractyl's own DB state in general, reducing how much of this category of problem needs
> per-pipeline compensating deletions in the first place.

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

> **[BACKLOG #16]** Planned: reverse the order in `reconcile_models` — currently, if
> `ollama_client.copy()` fails after `repo.create()` has already committed, an orphaned `models` row
> exists with no matching archived Ollama model behind it. Fix: `repo.create()` becomes a flush only
> (no commit) before `ollama_client.copy()` runs — a copy failure then lets the existing rollback
> machinery discard the never-committed DB row automatically. Separately: commit per tag rather than
> once for the whole batch — today, one tag failing late in a multi-tag reconciliation run would
> otherwise take down the already-successful earlier tags in the same batch too.

- **Known gap:** a model pulled outside the app (e.g. directly against the Ollama container) isn't
  archived or documented in `models` until some pull happens through the app — there's no scheduled,
  periodic check independent of that trigger. In practice this gap is narrower than it might sound:
  `reconcile_models()` iterates *every* locally present model on each run, not just the one just
  pulled — so any pull at all through the normal UI/API flow (not necessarily the same model that was
  pulled outside the app) sweeps up and archives every previously untracked model in the same pass.

- **Workaround today:** trigger any pull through `POST /ollama/models/pull` — pulling the same,
  already-current tag is cheap (Ollama's content-addressed pull mechanism fetches only the manifest,
  not the full model again), so this is a lightweight way to force a reconciliation pass on demand.
  *(Ollama's exact behavior here should be reconfirmed before relying on this in production — this is
  based on Ollama's general pull semantics, not something verified against this codebase.)*

> **[BACKLOG #15]** Planned: a periodic cleanup sweep for Ollama models that are (a) not under the
> `xtractyl-archive/` prefix, (b) whose digest is not in the `models` table, and (c) older than a
> configurable age guard (protecting the brief window between a legitimate pull completing and
> `reconcile_models()` archiving it) — closes the gap above, and specifically the risk of a model
> loaded directly against Ollama, bypassing the app, being selected by curl against
> `/prelabel_project` (though `enqueue_prelabel_job` already independently guards against this
> specific case today by resolving strictly against the `models` table, never against Ollama directly
> — see Prelabelling Pipeline).

### 3. `list_models` (`GET /ollama/models`)
- Reads directly from Ollama's `/api/tags`, filtered to names starting with `xtractyl-archive/` —
  no DB read here, stays a pure Ollama passthrough
- A model that failed to archive (reconciliation error, see step 1) never appears in this list —
  there's no separate "pending" state surfaced to the picker

### 4. Enqueueing a prelabelling run against an archived model
- `enqueue_prelabel_job` resolves the `archived_name` string sent by the frontend to a `models` row
  (`get_by_archived_name`) purely to obtain `model.id` for the `prelabelling_runs.model_id` FK
- The Redis status hash and the job payload pushed to the worker queue both carry the
  `archived_name` **string**, never the numeric id — Ollama and the worker/ml_backend chain only
  ever see the archived name, matching what `/api/generate` expects

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
  3. `model_repo.get_by_archived_name(cmd.model)` — `MODEL_NOT_FOUND` if the string isn't a known
     `archived_name`; a pure Postgres lookup, never checked against Ollama directly — this is what
     prevents a model that was pulled into Ollama but never archived via `reconcile_models()` from
     being usable here at all, even via direct API/curl access

> **[BACKLOG #23, partial]** `questions_and_labels` removed entirely from `EnqueueJobRequest`/
> `EnqueueJobCommand` — the client value is never read by `enqueue_prelabel_job` today (`qal` above is
> always the DB-sourced value), so it's pure dead weight subject to validation failures for no
> benefit. `GET /preview_qal` remains as a display-only lookup, unrelated to submission. (One piece of
> the larger Start Prelabelling bundle — dropdown, second-run guard, resume logic, and redundant
> hash/QAL column removal are the rest of #23, still to be worked through.)

> **New, not yet in the numbered backlog:** no check exists today for `projects.ls_tasks_uploaded`
> being `true` before enqueueing — a prelabelling run can currently be started against a project that
> was never uploaded to Label Studio at all. Planned: a `TASKS_NOT_UPLOADED` guard here, enforced
> server-side (not just left to the frontend dropdown below), consistent with the pattern already
> used elsewhere (see `project_exists`/`is_conversion_done` at Create Project) — a real backend check,
> not merely a UI-level filter.

- `prelabelling_runs` row created — `project`, `label_studio_id`, `questions_and_labels` (+ hashes),
  `model_id`, `system_prompt` (+ hash), `status="pending"`

> **Clarification on why `status` stays `"pending"` here, unlike `conversion_jobs.status` at the
> equivalent point:** for Conversion, all the work that can fail (file uploads, `files` rows) already
> happened *before* the status flip to `"converting"` (back in `prepare_conversion`) — by the time
> `start_conversion` runs, there's nothing left to resolve, only the conversion itself to perform. For
> Prelabelling, it's the other way around: the expensive, failure-prone resolution
> (`resolve_project_id`, `get_tasks_without_predictions` — both live Label Studio calls) happens
> *after* enqueueing, once the worker picks the job up (step 2). Flipping to `"running"` here, before
> that resolution has even been attempted, would collapse the distinction the planned `status` design
> deliberately preserves (see `prelabelling_runs.status` in the Schema Reference): a pre-loop
> resolution failure needs to read as `"pending"` → `"failed"` (the loop never started), not
> `"running"` → `"failed"` (which would incorrectly imply it had).

- Redis: a status hash (`status:<job_id>`) is set, and the job payload — `project_name`, `model`,
  `system_prompt`, `questions_and_labels` (the *client-submitted* value, not the `qal` just written to
  the DB row above — see `[BACKLOG #23, partial]` above), `token` — is pushed to the `prelabel_jobs`
  queue (Redis DB 0; separate from `conversion_jobs` in DB 1)

> **[BACKLOG #21, partial]** Planned: the Redis status hash (`state`/`progress`/`error` etc.) is
> dropped entirely, replaced by the `processed_tasks`/`total_tasks`/`cancel_requested` columns on
> `prelabelling_runs` (see Schema Reference) — job status becomes a Postgres read, not a Redis read.
> The job *payload* pushed to the queue is unaffected by this particular change and continues to
> exist; only the separate status hash goes away.

> **[BACKLOG #8]** Planned: `label_studio_id` added to the job payload — the orchestrator already
> resolved it above (step 1), so passing it along removes the worker's redundant `resolve_project_id`
> call in step 2.

- The Redis payload does **not** include `label_studio_id`, even though the orchestrator just
  resolved it — the worker re-resolves it independently via an extra Label Studio API call
  (`resolve_project_id`) purely because it wasn't passed along *(current behavior; see [BACKLOG #8]
  directly above for the planned fix)*

> **New, not yet in the numbered backlog — frontend project-selection endpoint:** a new
> `GET /list_projects_ready_for_prelabelling` (mirroring the pattern from Upload Tasks/Create Project)
> returns projects with `ls_tasks_uploaded = true` **and** no existing `prelabelling_runs` row with
> `status` in (`pending`, `running`, `done`) — matching the server-side guard from
> Planned Changes point 5 exactly (a `failed` run remains selectable, routed into resume rather than
> excluded). Replaces free-text project entry in the frontend with a dropdown, consistent with the
> UI pattern used everywhere else in the app.

### 2. Worker pulls the job, validates the task list, resolves what to process

> With [BACKLOG #8] implemented, `resolve_project_id` is no longer called here — `label_studio_id`
> arrives directly in the job payload, resolved once already by the orchestrator in step 1.

- Task openness (which tasks still need processing) is determined from Postgres, not Label Studio's
  live state — a task counts as open if it has no `task_prelabelling_metas` row with
  `status="success"` under this run's id (Planned Changes point 5) — this is what makes resume
  correct even if someone manually deleted a prediction directly in Label Studio, since Postgres, not
  Label Studio, is the source of truth for "is this task done"

> **Pre-loop validation, before any task reaches the LLM-processing loop (step 3):** for each
> candidate task from the DB-open list above, two checks run, and either one failing writes a
> `task_prelabelling_metas` row directly here — `status="failed"`, with `error` populated — rather
> than proceeding into the main loop for that task. This is the only insert point for such a row
> other than the normal end-of-task write in step 3; both paths write to the same table under the
> same "insert once, never updated" rule.
>
> 1. **Filename match [BACKLOG #19]:** the task is matched against
>    `files.filename` for this project; no match → `error` describes it as an unrecognized/manually
>    created Label Studio task, not something Xtractyl uploaded
> 2. **Label Studio/DB coherence check (new):** the task's live state in Label Studio is checked
>    against the DB's "open" determination above — if Label Studio already shows a prediction for a
>    task the DB considers open, that's a contradiction (not simply reprocessed, since running the LLM
>    again would add a second, overlapping prediction on top of the existing one, without replacing
>    it); `error` explains that this task was prelabelled independently in Label Studio, outside of
>    Xtractyl, and points the user at Label Studio to resolve the conflict directly (e.g. deleting the
>    stray prediction there) before this task can be reprocessed through the app
>
> Both cases count toward `processed_tasks` (Planned Changes point 4) like any other outcome — a run
> containing either kind of pre-loop failure therefore lands on `"incomplete"`, not `"done"`, once
> all tasks are accounted for (see `prelabelling_runs.status` in the Schema Reference).

### 3. Per task: `send_predict` → ml_backend `/predict`
- The worker already holds the task's HTML in memory from the bulk fetch in step 2, so it's passed
  directly in the request body — no second Label Studio round-trip per task
- ml_backend (`run_predict`): extracts the DOM via a freshly-launched headless Chromium
  (Playwright) per task, converts the HTML to plain text via BeautifulSoup for the LLM prompt, asks
  Ollama once per question (`temperature=0, seed=42` for reproducibility), then matches each answer
  back into the DOM (`extract_xpath_matches_from_dom`) to ground it in an actual document location —
  this grounding check is the closest thing the system has to hallucination detection

> **[BACKLOG #5]** Planned: `attach_meta_to_task` removed entirely. It has no live reader
> (`_latest_prediction_meta`/`ml_meta` exists in the code but is only reachable via
> `_tasks_to_rows(mode="pred")`, which is never actually called — only `mode="gt"` is). Predictions
> still get written to Label Studio (for human review); the meta does not need a second write there.

- ml_backend writes to Label Studio: `save_predictions_to_labelstudio` (the actual prediction) *(and,
  until [BACKLOG #5] lands, `attach_meta_to_task` — see above)*
- The worker then forwards the returned `meta` to the orchestrator (`send_task_meta` /
  `POST /prelabel/task-meta`), which is what actually persists it into `task_prelabelling_metas` —
  neither the worker nor ml_backend has any direct Postgres access anywhere in the codebase

> **[BACKLOG #3]** Planned: `wait_until_prediction_saved` removed. The worker currently also polls
> Label Studio again (up to 15 minutes) to confirm the prediction landed — redundant, since
> ml_backend's own write is already synchronous and raises on failure before ever returning a
> response, and in direct tension with the principle below that Label Studio's live state is no
> longer trusted as a source of truth once [BACKLOG #20] lands.

> **[BACKLOG #2]** Planned: `task_prelabelling_metas` gains `status` (`success`/`failed`) and `error`
> columns — the table currently has no explicit success/failure field at all, every row implicitly
> represents a successful task today. Three outcomes: a timeout (or any other failure covered by
> [BACKLOG #9] below) on any single question fails the whole task, nothing written to Label Studio;
> DOM matching that runs but finds nothing is still `status="success"` (plus a `no_dom_match` flag);
> DOM extraction/matching itself crashing is `status="failed"`. The retry/resume filter (Planned
> Changes point 5 / Prelabelling Pipeline step 2) checks specifically for `status="success"` — a
> `failed` row does not block a future retry of that task.
>
> This requires a compensating transaction: if a prediction is successfully written to Label Studio
> but the corresponding Postgres write (the `send_task_meta`/`task-meta` call above) fails — even
> after retry — the Label Studio prediction is deleted again, so the two never permanently disagree.
> Needs `save_predictions_to_labelstudio` to capture the created prediction's ID (currently discarded)
> so it can be targeted for deletion.

> **[BACKLOG #9, concretized]** `ask_llm_with_timeout` (`ml_backend/infrastructure/ollama.py`) today:
> ```python
> except requests.exceptions.Timeout:
>     return {"answer": None, "status": "timeout", "error": "timeout"}
> except Exception as e:
>     return {"answer": None, "status": "error", "error": str(e)}
> ```
> Two problems, not one: (a) `num_ctx` is accepted as a parameter (and already arrives correctly via
> a worker-level env var, `LLM_NUM_CTX`) but is never actually included in the `options` dict sent to
> Ollama — a one-line fix; (b) only `status == "timeout"` is checked downstream (`predict.py`) to
> decide whether a task failed — a genuine code bug (e.g. a `KeyError`) is caught by the blanket
> `except Exception`, returns `status="error"` instead of `"timeout"`, and is therefore **not**
> treated as a failure at all: the answer for that one question silently becomes `None` and the loop
> continues, indistinguishable from a legitimate empty response — it doesn't even increment
> `n_timeouts` in `PerfCollector`, since that counter also only checks for `status=="timeout"`. *(This
> corrects the original phrasing of this point, which described the risk backwards — as a bug being
> mistaken for a timeout, rather than a bug being silently swallowed as an ignored non-failure.)*
>
> Fix: narrow the second except clause to `requests.exceptions.RequestException` (covers
> `ConnectionError`, `HTTPError` from `raise_for_status()`, and other genuine external-call failures)
> — a real code bug is then no longer caught here at all, and propagates as an actual exception into
> the per-task retry-with-backoff logic from [BACKLOG #21]/[BACKLOG #22] instead of disappearing.
> `JSONDecodeError` deliberately not added to this clause — Ollama has never been observed returning
> malformed JSON on a 2xx response, and `raise_for_status()` already catches non-2xx before `.json()`
> is ever called, so a JSON-decode branch would guard against a failure mode with no known precedent.
> Both `Timeout` and the broadened `RequestException` branch now return `status="failed"` (not
> `"timeout"`/`"error"` as two different strings) — `error` remains `"timeout"` for the `Timeout` case
> specifically, `str(e)` for the rest — so the downstream check in `predict.py` becomes a single
> `status == "failed"` condition instead of only matching the literal string `"timeout"`.

> **[BACKLOG #10]** Planned: `dom_match.py` gains a guard for LLM answers that normalize to an empty
> string — currently only the raw (pre-normalization) answer is checked for emptiness, and Python's
> `str.find("")` always returns `0`, which combined with negative-index wraparound on the offset map
> (`index_map[-1]`) produces a spurious, silent false match rather than a correct "not found".

- `dom_ms` is computed in ml_backend's `PerfCollector` output but has no corresponding column and no
  reader anywhere — trivially derivable from `task_ms_dom_extract` + `task_ms_dom_match`, both of
  which *are* stored

> **Clarification — `"incomplete"` is never set eagerly, mid-loop:** see the "no eager flip"
> clarification under step 4 below for the full reasoning; the short version is that a task failing
> here does not by itself change `prelabelling_runs.status` — only the progress callback's own
> completion check (step 4) or the stale-run sweep (also step 4) does.

### 4. Job completion / cancellation

**Current mechanism (today):**
- `handle_prelabel_callback` (`POST /prelabel/callback`) sets `prelabelling_runs.status` to `"done"`,
  `"failed"`, or `"cancelled"` — this is a *separate* callback from the per-task one in step 3, fired
  once after the worker's task loop ends
- On `"done"`: triggers `sync_missing_evaluations` (see Evaluation Pipeline) — this and
  `save_as_gt_set` are the only two triggers for this function; it is deliberately not exposed as its
  own route to prevent a user from forcing an evaluation to (re-)compute on demand
- Cancellation: `POST /prelabel/cancel/:id` sets `state="CANCEL_REQUESTED"` in the *same* Redis status
  hash from step 1; the worker checks this once per task-loop iteration (`cancel_cb`)
- Redis `logs:<job_id>` is written throughout the worker run (`_add_log`) but never read anywhere;
  `result:<job_id>` (just `{"logs_count": ...}`) is included in `get_job_status`'s response but the
  frontend never reads it either

> **[BACKLOG #21]** Planned: job-level status/progress/cancel moves from Redis to Postgres, mirroring
> how Conversion already works — new `processed_tasks`, `total_tasks`, `cancel_requested` columns on
> `prelabelling_runs` (see Schema Reference for exact Set/Changed semantics). `total_tasks` is set
> once, from the worker's own task-list length, on the *first* progress call of a given run (needed
> because a resumed run's true task count can be smaller than the project's full document count —
> Planned Changes point 5 / Prelabelling Pipeline step 2). The dead Redis keys (`logs:`, `result:`,
> and the status hash itself) are dropped outright.

> **[BACKLOG #22]** Planned: callback consolidation — the per-task callback from step 3
> (`send_task_meta` / `/prelabel/task-meta`) is renamed to `send_task_progress` /
> `/prelabel/progress`, and becomes the **only** callback that matters for the common case. It takes
> over two responsibilities previously split across the two separate callbacks:
> - **Completion detection:** `processed_tasks` is incremented atomically per task (regardless of
>   that task's success/failure), and the same call checks `processed_tasks >= total_tasks` — if
>   true, `status` transitions to its terminal value right there (`"done"` if every task succeeded,
>   `"incomplete"` if at least one didn't — see `prelabelling_runs.status` in the Schema Reference for
>   the full transition table), and `sync_missing_evaluations` fires on `"done"` from this same call
> - **Stop signal:** the response includes `{"should_stop": bool}`, derived from `cancel_requested`
>   — replacing the separate `cancel_cb` polling loop against the Redis status hash
>
> **Retry-with-backoff replaces run-wide abort on single-task failure:** each task's
> `send_predict` + `send_task_progress` gets its own try/except with retry-with-backoff, instead of
> any exception bubbling out and killing the entire run. Today's actual behavior here is already
> inconsistent — a non-200 ml_backend response is logged and shrugged off, while a raised exception
> (e.g. a dropped connection) kills the whole run outright; the retry-with-backoff approach replaces
> both with one consistent, non-fatal-per-task behavior.
>
> **The old end-of-job callback (`handle_prelabel_callback` / `POST /prelabel/callback`) is kept, but
> narrowed** to the one case counting can't detect: an exception before the task loop even starts
> (project/task-list resolution itself failing, per Prelabelling Pipeline step 2) — reported via a
> distinct payload shape without a `task_id`. This is also the only remaining path to `status="failed"`
> — see the `"pending"` → `"failed"` transition (skipping `"running"` entirely) already described
> under `prelabelling_runs.status` in the Schema Reference. `"cancelled"` is set via this same
> narrowed callback when the worker's loop exits early due to `should_stop` — the loop still needs to
> report that it stopped, even though counting alone can't distinguish "stopped due to cancellation"
> from "stopped due to still being mid-run".

> **⚠️ Insert — Stale `"running"` run sweep (new, not yet in the numbered backlog)**
>
> Covers the case where the worker process itself crashes mid-loop — no task ever reaches
> `status="failed"` for the normal reason (retries exhausted, per [BACKLOG #2] in step 3), because
> nothing is left running to exhaust them; `processed_tasks` simply stops advancing forever, and
> neither the progress callback nor the narrowed end-of-job callback above will ever fire again to
> make the done/incomplete/failed determination.
>
> The same cleanup container already covering Conversion's stale-job sweep (see the Insert after
> `conversion_jobs` in the Schema Reference) additionally sweeps `prelabelling_runs` rows stuck at
> `status="running"` whose `updated_at` is older than a configurable age guard — mirroring the exact
> mechanism already used for `conversion_jobs` (`CLEANUP_STALE_AFTER_HOURS`, checked against
> `updated_at`, which is bumped on every `processed_tasks` increment same as
> `conversion_jobs.converted_files`). A caught run is set to `"incomplete"` directly by the sweep —
> not `"failed"` — since the tasks that did complete before the crash are still valid, successfully
> processed tasks, exactly like a normal `"incomplete"` run; only the *reason* differs (crash vs.
> individual task failures), which the sweep doesn't need to distinguish for the resulting state to
> be correct.
>
> **Why this can only be a sweep, not something the run itself detects:** by definition, nothing is
> left executing to perform this check from inside the crashed run — the worker that would normally
> reach the completion condition is the thing that's gone.
>
> **Clarification — no eager `"incomplete"` flip:** even once an individual task fails (per
> [BACKLOG #2] in step 3), `status` stays `"running"` until either the progress callback's own
> `processed_tasks >= total_tasks` check fires, or this stale-run sweep catches a crashed one — never
> flipped the moment a single task fails. An eager flip was considered and rejected: with multiple
> users/processes able to interact with a run, it could let a second enqueue attempt for the same
> project slip past the [BACKLOG #23] second-run guard while the run is still genuinely in progress,
> if `"incomplete"` were ever treated the same as a terminal state by that guard.

---

### Planned Changes (Prelabelling Pipeline) — resolution

The original numbered list (points 1–11) has been fully worked through and incorporated into the
pipeline steps above: points 1, 3, 4, 5, 6, 7, 8, 9, 10 are embedded as `[BACKLOG #X]` blockquotes at
their correct workflow location (steps 1–4); point 2 is split across `[BACKLOG #2]` and `[BACKLOG #5]`
in step 3. Point 11 is resolved below as dropped.

> **[BACKLOG #26] — dropped, not pursued.** Originally proposed as a completeness/traceability check
> hashing Label Studio's live `data.html` against `files.html_hash` before a prelabelling run starts.
> Verified: Label Studio does support in-place editing of an existing task's `data` field via
> `PATCH /api/tasks/:id/` without changing the task's id — so task-id/filename stability alone does
> not guarantee content stability. However, this capability isn't exposed through the documented Data
> Manager GUI (deletion, filtering, and annotation are, direct data-content editing is not) — only
> through direct API access. Given that the threat model here is GUI-level usage, not deliberate API
> tampering (which would have far more direct routes to cause harm, e.g. direct DB/MinIO access), this
> check isn't pursued. Note for later: Label Studio serves its UI and REST API from the same origin
> (no way to expose the frontend without the API) — a planned login gate in front of Label Studio
> restricts who reaches it at all, but doesn't change what an already-authorized user could do once
> inside, so it doesn't itself revisit this decision.

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
- `run_repo.get_latest_run(cmd.project_name)` — resolves the project name to a `prelabelling_runs`
  row; raises `RUN_NOT_FOUND` if none exists
- Reads `task_prelabelling_metas` for that run, flattens `raw_llm_answers` into one column per label
  (`<label>__pred`), returns a table: `task_id`, `filename`, one predicted-answer column per label
- **DB-only, not a Label Studio passthrough** — despite what the route's own OpenAPI contract and
  auth requirement suggest (see the two stale-artifact findings below), this function never calls
  Label Studio at all; it reads exclusively from Postgres via `PrelabellingRunRepository`. This
  appears to be a completed migration (see README, Phase 2: "Migration of filesystem-based state to
  Postgres and MinIO" — marked Completed) whose cleanup was left unfinished at this route
- No filtering by `status` — every row in `task_prelabelling_metas` for the run is included. Once
  [BACKLOG #25] restricts the selectable projects to `status="done"` runs only (see below), this
  stops being an open question: a `"done"` run cannot contain a `status="failed"` row by definition
  (any failed task would have made the run `"incomplete"` instead), so a table backing a `"done"` run
  is guaranteed to contain only successful task rows — no separate filtering/flagging logic is needed
  for this table itself.

> **New, not yet in the numbered backlog — legacy artifact cleanup at this route:**
> - The route requires a Label Studio token (`TOKEN_REQUIRED` if missing), but `cmd.token` is never
>   passed into or used by `build_results_table` — dead requirement, left over from before the
>   DB migration; the code itself flags this (`# remove when removing legacy route`). Planned:
>   drop the token requirement from this endpoint entirely.

> **Known issue (shared with Evaluation Pipeline):** `get_latest_run` has no status filter — it
> returns whatever `prelabelling_runs` row is newest for the project, regardless of status. A project
> with a finished, evaluated `"done"` run, followed by a second run that ends up `"failed"` or
> `"incomplete"`, would have this resolve to the second (wrong) run instead of the one with usable
> results. See the same issue described under Evaluation Pipeline, and [BACKLOG #24] for the planned
> fix — the [BACKLOG #23] second-run guard is what makes this practically unreachable going forward,
> same as for Evaluation.

> **[BACKLOG #25]** Planned: free-text project entry replaced with a dropdown, filtering to projects
> with a `prelabelling_runs` row at `status="done"` only — `"incomplete"`, `"failed"`, `"cancelled"`,
> `"pending"`, and `"running"` runs are all excluded, not just non-terminal ones. This is stricter
> than [BACKLOG #23]'s Prelabelling-start dropdown (which also surfaces `"failed"` runs, tagged for
> resume) — here, the run has to actually be usable as a finished result, not merely resumable.
> Backed by a new DB-only endpoint (no Label Studio involvement needed, per the DB-only finding
> above) — filters `prelabelling_runs` by project and `status="done"` directly.

---

## Evaluation Pipeline (`evaluate-ai`, `save-as-gt-set`)

**`save_as_gt_set`** (`POST /save-as-gt-set`): reads live from Label Studio (task list + chosen
annotations), writes `task_groundtruth_annotations` and flips `projects.is_groundtruth`. No Label
Studio writes happen here at all — only reads — so unlike Create Project/Upload Tasks there is no
orphaned-external-resource risk to compensate for; the DB writes are already covered by the same
commit/rollback-per-request pattern used everywhere else. Triggers `sync_missing_evaluations`
afterward (a new GT set may now retroactively match existing done runs).

**`evaluate_run`** (the only place an evaluation is actually computed/persisted): guards against
label-set mismatch (`labels_hash`) and non-identical document sets (`html_hash` set equality,
exact — a 40/41-identical overlap does not qualify) before computing metrics via
`compute_metrics_from_rows` and saving to `evaluations`. Deliberately takes an explicit `run_id`
rather than resolving "latest run" for a project, specifically to avoid the ambiguity described
next.

**`sync_missing_evaluations`**: the only two triggers are a run reaching `"done"` and a new GT set
being saved; deliberately not exposed as its own route (see Prelabelling Pipeline). Matches purely
on `(labels_hash, document_set_hash)` — `questions_hash`, `system_prompt`, and the model used play no
role in *whether* an evaluation gets created, only in how Comparison/Regression/Drift later group the
results that exist.

> **[BACKLOG #24, resolved by design rather than by patching]** `get_latest_run` (the repository
> method backing this pipeline, plus `resolve_family_for_project` and `build_results_table`) has no
> status filter today — it returns whatever `prelabelling_runs` row is newest for a project,
> regardless of `status`. Originally scoped as either adding a status filter or moving all three call
> sites to an explicit `run_id`. With the `UNIQUE` constraint on `prelabelling_runs.project` (see
> Schema Reference, under `prelabelling_runs`) in place, this ambiguity cannot arise at all — there is
> never more than one row per project to choose between, "latest" stops being a meaningful concept,
> and no separate status-filter fix or call-site rework is needed. The only remaining action is
> cosmetic: rename `get_latest_run` to something that doesn't imply a choice among candidates (e.g.
> `get_run_for_project`), and update its callers accordingly. No defense is planned against the
> constraint itself being bypassed (e.g. a raw SQL migration circumventing it) — considered
> out of scope, the same category of risk as someone directly corrupting the database, which nothing
> in the application layer can meaningfully guard against.

> **[BACKLOG #11]** Planned: `compute_metrics_from_rows` currently classifies a task/label pair as a
> true negative whenever the ground truth is empty and the prediction is any falsy value — not
> specifically the `<<<NO_MATCH>>>` sentinel the system prompt is supposed to enforce. In practice,
> the ambiguity this could cause is expected to be rare: once [BACKLOG #9]/[BACKLOG #2] land, any
> exception-driven empty answer fails the whole task rather than silently producing `None` for one
> question, and a genuinely empty (non-erroring, `status="ok"`) LLM response is, per experience
> running these models, essentially never observed in practice — models reliably produce *some* text
> even when explicitly instructed to answer with nothing. This is a cheap, purely defensive fix for a
> theoretical edge case that both changes above make unlikely, not a response to an actively observed
> problem. Fix: require the literal sentinel for the TN classification.

> **New, not yet in the numbered backlog — comparison run restricted to `"done"`:** both the frontend
> selection (a new dropdown for the comparison project, mirroring [BACKLOG #25]'s Get Results
> dropdown) and `evaluate_run` itself gain a `status == "done"` requirement for the
> `comparison_prelabelling_run_id` being evaluated — today, `evaluate_run` checks `is_groundtruth`,
> run existence, `labels_hash` match, and document-set equality, but nothing about the comparison
> run's own status. A direct API call bypassing the dropdown could otherwise evaluate a `"failed"`,
> `"incomplete"`, `"cancelled"`, `"running"`, or `"pending"` run today. Restricting to `"done"` is the
> more structural fix for the TN ambiguity above too: a `"done"` run cannot contain a
> `status="failed"` task row by definition (Schema Reference, `prelabelling_runs.status`), so this
> also rules out the exception-driven half of [BACKLOG #11]'s concern by construction, the same way
> it already does for Get Results.

> **[BACKLOG #4]** Planned: `EvaluationRepository.list_configurations_for_labels` and
> `.list_evaluation_series` removed — fully implemented (including a non-trivial grouped/having
> query) but have no caller anywhere in the codebase.

> **Planned:** internal ground truth sets — a ground truth scoped to, and only ever compared against,
> the single prelabelling run it was created for (never against other projects with the same
> documents/labels). Not yet scoped in detail; will need its own review pass before implementation,
> touching at minimum: the `projects.is_groundtruth` → categorical change already noted in the Schema
> Reference, `sync_missing_evaluations` (must not scan internal GTs the way it scans external ones),
> and the Comparison/Regression/Drift peer-grouping logic below (must filter on scope in addition to
> configuration, so an internal-GT project can never appear in the same comparison group as an
> external one).

---

## Evaluation Drift, Regression, Comparison

Read-only across all three views — no writes. All three resolve an arbitrary project name to its
underlying `(groundtruth_project, run)` pair via the shared `resolve_family_for_project` (inherits the
`get_latest_run` caveat above — see `[BACKLOG #24, resolved by design rather than by patching]` under
Evaluation Pipeline: the `UNIQUE` constraint on `prelabelling_runs.project` means there is never more
than one row to resolve to, so this inherited ambiguity resolves the same way here, no separate fix
needed at these three call sites). Beyond that shared dependency, reviewed without further findings:

- **Comparison** (`get_comparison_view`): every evaluation against one fixed groundtruth project,
  regardless of configuration — the broadest of the three views.
- **Regression** (`get_regression_view`): filters to the *exact same* configuration
  (`labels_hash`, `questions_hash`, `model_digest`, `system_prompt_hash`) against the same
  groundtruth project, ordered by time — only the model/prompt/questions staying fixed while time
  varies counts.
- **Drift** (`get_drift_view`): same configuration, but *different* groundtruth projects with
  provably zero document overlap between them (exact set intersection on `html_hash`, not just a
  different aggregate `document_set_hash` — a 40/41-identical overlap is correctly excluded). Since
  "no overlap" isn't a transitive relation, there is no single natural grouping once more than two
  compatible groundtruth projects exist for a configuration — `_find_best_drift_chain` finds the
  largest overlap-free chain containing the selected project via brute-force
  `itertools.combinations`, deliberately simple since the candidate set is already pre-filtered to
  one configuration.