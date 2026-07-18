from sqlalchemy import text
from utils.logging_utils import safe_logger


def cleanup_stale_conversion_jobs(db, storage, stale_after_hours: int = 2) -> int:
    stale_projects = (
        db.execute(
            text("""
        SELECT project FROM conversion_jobs
        WHERE (status = 'pending'
                AND created_at < now() - make_interval(hours => :h))
           OR (status IN ('converting', 'failed')
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
                WHERE project = :p AND status IN ('pending', 'converting', 'failed')
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
