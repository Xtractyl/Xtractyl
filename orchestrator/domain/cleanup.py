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
