# API Standards (GET / POST)

This document defines the request/response conventions for the orchestrator API.
Goal: consistent endpoint behavior, predictable auth handling, and easier validation via API contracts.

---

## GET (Read-only)

- **Purpose:** Read data only (no side effects).
- **Parameters:**
  - Resource IDs in the **path**: `/jobs/{job_id}`
  - Filtering/pagination in the **query string**: `?from=0&limit=50`
- **Auth:**
  - Always via header: `Authorization: Bearer <token>`
  - No tokens in query parameters (except temporary migration fallback)
- **Responses:**
  - `200 OK` (returns data)
  - `404 Not Found` (resource does not exist)
  - `400 Bad Request` (invalid query params)

---

## POST (Create / Start / Compute / Actions)

- **Purpose:** Create resources, trigger actions, start jobs, run computations.
- **Request body:**
  - Always `Content-Type: application/json`
  - Use a **flat JSON body** (no `data` wrapper), e.g.:
    ```json
    { "project_name": "...", "...": "..." }
    ```
- **Auth:**
  - Always via header: `Authorization: Bearer <token>`
  - Do not send tokens in the JSON body (except temporary migration fallback)
- **Responses:**
  - `200 OK` for “compute/action result”
  - `201 Created` for “resource created”
  - `202 Accepted` for async job started (returns a job id)
  - `400 Bad Request` for validation errors
  - `401 Unauthorized` token missing/invalid
  - `403 Forbidden` token valid but insufficient permissions

---

## Naming / Routing

- **No verbs in routes:** avoid `/get_results_table`, use `/results/table`
- Use **plural resources:** `/projects`, `/jobs`
- Use **sub-resources:** `/jobs/{id}/logs`, `/projects/{name}/tasks`

---

## Compatibility Phase (no breaking changes)

- Keep old endpoints as **aliases** temporarily.
- Token fallback order:
  1) `Authorization` header (new standard)
  2) `token` in JSON body or query params (legacy)


  ---

---

## Standard Field Names (Requests + Responses)

This section defines the canonical field names used in API requests and responses.

### Requests

Auth
- token (legacy only, temporary fallback)
- Preferred: Authorization: Bearer <token> (HTTP header)

Project
- project_name (string)

Evaluation
- groundtruth_project (string)
- comparison_project (string)

Jobs / Logs
- job_id (string) — always in path: /jobs/{job_id}
- from (int) — log offset in query: /jobs/{job_id}/logs?from=0

Generic conventions
- Use snake_case for all JSON keys and query params.
- Avoid abbreviations unless already established (gt_name → use groundtruth_project).

---

### Responses

All endpoints should return JSON.

Success response (recommended)
- status: "ok"
- data: any (payload)

```json
{
  "status": "ok",
  "data": {}
}
``` 

Error response (recommended)
- status: "error"
- error: string (human-readable message)
- details: optional (validation details, debug info)

```json
{
  "status": "error",
  "error": "project_name is required",
  "details": []
}
``` 

Job responses (async)
- status: "ok"
- job_id: string

```json
{
  "status": "ok",
  "job_id": "abc123"
}
``` 

Results table response
- status: "ok"
- data: table payload (implementation-specific)

```json
{
  "status": "ok",
  "data": [
    { "field": "value" }
  ]
}
``` 