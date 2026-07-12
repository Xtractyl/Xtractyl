from sqlalchemy import text
from utils.logging_utils import safe_logger


def cleanup_stale_conversion_jobs(db, storage, stale_after_hours: int = 2) -> int:
    stale_projects = (
        db.execute(
            text("""
        SELECT project FROM conversion_jobs
        WHERE status = 'pending'
          AND created_at < now() - make_interval(hours => :h)
    """),
            {"h": stale_after_hours},
        )
        .scalars()
        .all()
    )

    count = 0
    for project in stale_projects:
        result = db.execute(
            text("""
            DELETE FROM conversion_jobs
            WHERE project = :p AND status = 'pending'
            RETURNING id
        """),
            {"p": project},
        )
        if not result.fetchone():
            continue

        storage.delete_prefix(project)
        db.execute(text("DELETE FROM files WHERE project = :p"), {"p": project})
        db.execute(text("DELETE FROM projects WHERE name = :p"), {"p": project})
        count += 1
        safe_logger.info("stale_project_cleaned | project=%s", project)

    db.commit()
    return count
