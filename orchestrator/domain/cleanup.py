from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from utils.logging_utils import safe_logger


def cleanup_stale_conversion_jobs(db, storage, stale_after_hours: int = 2) -> int:
    stale_projects = (
        db.execute(
            text("""
        SELECT project FROM conversion_jobs
        WHERE (status = 'pending'
                AND created_at < now() - make_interval(hours => :h))
           OR (status IN ('converting', 'failed', 'cancelled')
                AND updated_at < now() - make_interval(hours => :h))
    """),
            {"h": stale_after_hours},
        )
        .scalars()
        .all()
    )

    count = 0
    for project in stale_projects:
        try:
            result = db.execute(
                text("""
                DELETE FROM conversion_jobs
                WHERE project = :p AND status IN ('pending', 'converting', 'failed', 'cancelled')
                RETURNING id
            """),
                {"p": project},
            )
            if not result.fetchone():
                db.rollback()
                continue

            db.execute(text("DELETE FROM files WHERE project = :p"), {"p": project})
            db.execute(text("DELETE FROM projects WHERE name = :p"), {"p": project})
            db.commit()  # DB state for this project is now safely persisted...

            storage.delete_prefix(project)  # ...before we touch the irreversible MinIO side
            count += 1
            safe_logger.info("stale_project_cleaned | project=%s", project)
        except Exception:
            db.rollback()
            safe_logger.error("stale_project_cleanup_failed | project=%s", project)
            continue

    return count


def sweep_orphaned_storage_prefixes(db, storage) -> int:
    prefixes = storage.list_top_level_prefixes()
    known_projects = {row[0] for row in db.execute(text("SELECT name FROM projects")).all()}

    count = 0
    for prefix in prefixes:
        if prefix in known_projects:
            continue
        try:
            storage.delete_prefix(prefix)
            count += 1
            safe_logger.info("orphaned_storage_prefix_cleaned | prefix=%s", prefix)
        except Exception:
            safe_logger.error("orphaned_storage_prefix_cleanup_failed | prefix=%s", prefix)
            continue

    return count


def sweep_unarchived_ollama_models(
    db, ollama_client, archive_prefix: str, min_age_hours: int = 24
) -> int:
    known_digests = {row[0] for row in db.execute(text("SELECT digest FROM models")).all()}

    try:
        tags = ollama_client.list_tags()
    except Exception:
        safe_logger.error("ollama_orphan_sweep_list_failed")
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=min_age_hours)
    count = 0
    for entry in tags:
        name = entry.get("model") or entry.get("name")
        digest = entry.get("digest")
        if not name or name.startswith(f"{archive_prefix}/"):
            continue
        if digest and digest in known_digests:
            continue
        modified_at_raw = entry.get("modified_at")
        try:
            modified_at = datetime.fromisoformat(str(modified_at_raw).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if modified_at > cutoff:
            continue
        try:
            ollama_client.delete(name)
            count += 1
            safe_logger.info("orphaned_ollama_model_cleaned | name=%s", name)
        except Exception:
            safe_logger.error("orphaned_ollama_model_cleanup_failed | name=%s", name)
            continue

    return count


def sweep_orphaned_label_studio_projects(
    db, label_studio, admin_token: str, min_age_hours: float = 0.5
) -> int:
    """compares Label Studio's own project list against projects.label_studio_id
    and deletes anything unmatched that is older than a cutoff. A cutoff is necessary
    because the db can not have the label studio ID before saving in label studio,
    so any project will be an orphan for a short time and even if we could have the ID
    beforehand we should only commit in the db after successful saving in label studio
    as the latter is the more fragile process, the default time to delete (after 30min)
    is orders of magnitudes larger than the time it should normally take between
    saving in label studio and committing in db (normally miliseconds)
    """
    if not admin_token:
        safe_logger.error("label_studio_orphan_sweep_skipped | reason=no_admin_token")
        return 0

    known_ids = {
        row[0]
        for row in db.execute(
            text("SELECT label_studio_id FROM projects WHERE label_studio_id IS NOT NULL")
        ).all()
    }

    try:
        ls_projects = label_studio.list_projects(admin_token)
    except Exception:
        safe_logger.error("label_studio_orphan_sweep_list_failed")
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=min_age_hours)
    count = 0
    for p in ls_projects:
        project_id = p.get("id")
        if project_id is None or project_id in known_ids:
            continue
        created_at_raw = p.get("created_at")
        try:
            created_at = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            # Unparseable timestamp — treat conservatively as "too new to touch".
            continue
        if created_at > cutoff:
            continue
        try:
            label_studio.delete_project(project_id, admin_token)
            count += 1
            safe_logger.info("orphaned_label_studio_project_cleaned | project_id=%s", project_id)
        except Exception:
            safe_logger.error(
                "orphaned_label_studio_project_cleanup_failed | project_id=%s", project_id
            )
            continue

    return count


STALE_RUN_ERROR = (
    "[WORKER_LOST] No progress for longer than the task timeout allows; "
    "the worker has probably crashed. Resume the run to continue."
)


def sweep_stale_prelabelling_runs(
    db,
    per_question_seconds: int,
    margin_seconds: int,
    factor: float = 2,
) -> int:
    """Sets prelabelling runs that stopped receiving task results from "running" to "incomplete".

    updated_at of a run is bumped by every task result, so it is the heartbeat. One task cannot
    take longer than the worker's request timeout (questions * (LLM_TIMEOUT + LLM_OVERHEAD) +
    UPLOAD_MARGIN); a run silent for `factor` times that has no task left in flight (the worker
    is gone). "incomplete" keeps the finished tasks and the run can be resumed like any other
    incomplete run. Only "running" is touched: "pending" never had a heartbeat to compare with.

    The status is checked again inside the UPDATE, so a task result arriving at the same moment
    wins the row lock and the run is left alone.
    """
    try:
        rows = db.execute(
            text("""
            UPDATE prelabelling_runs AS r
            SET status = 'incomplete', error = :error, updated_at = now()
            FROM projects AS p
            WHERE p.name = r.project
              AND r.status = 'running'
              AND r.updated_at < now() - make_interval(
                    secs => :factor * (
                        GREATEST(1, COALESCE(jsonb_array_length(p.questions_and_labels->'questions'), 1))
                        * :per_question + :margin
                    )
                  )
            RETURNING r.id, r.project
        """),
            {
                "error": STALE_RUN_ERROR,
                "factor": factor,
                "per_question": per_question_seconds,
                "margin": margin_seconds,
            },
        ).all()
        db.commit()
    except Exception:
        db.rollback()
        safe_logger.error("stale_run_sweep_failed")
        return 0

    for run_id, project in rows:
        safe_logger.warning("stale_run_set_incomplete | run=%s project=%s", run_id, project)
    return len(rows)
