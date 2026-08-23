# orchestrator/domain/model_reconciliation.py
import os
import time

from utils.logging_utils import safe_logger

ARCHIVE_PREFIX = os.getenv("XTRACTYL_MODEL_ARCHIVE_PREFIX", "xtractyl-archive")


def _sanitize(name: str) -> str:
    return name.replace(":", "-").replace("/", "-")


def reconcile_models(repo, ollama_client, pulled_via: str = "user_pull") -> int:
    tags = ollama_client.list_tags()
    archived_count = 0
    errors: list[str] = []

    for entry in tags:
        name = entry.get("model") or entry.get("name")
        digest = entry.get("digest")
        if not name or not digest or name.startswith(f"{ARCHIVE_PREFIX}/"):
            continue

        try:
            existing = repo.get_by_digest(digest)
            if existing:
                repo.touch(existing.id)
                repo.commit()
                continue
            details = entry.get("details") or {}
            short_digest = digest.replace("sha256:", "")[:12]
            timestamp = time.strftime("%Y%m%d%H%M%S")
            archived_name = f"{ARCHIVE_PREFIX}/{_sanitize(name)}:{short_digest}-{timestamp}"

            ollama_client.copy(source=name, destination=archived_name)
            repo.create(
                tag=name,
                digest=digest,
                archived_name=archived_name,
                size_bytes=entry.get("size"),
                family=details.get("family"),
                parameter_size=details.get("parameter_size"),
                quantization_level=details.get("quantization_level"),
                ollama_version=None,
                pulled_via=pulled_via,
            )
            repo.commit()
            archived_count += 1
        except Exception as e:
            repo.rollback()
            safe_logger.error("model_reconciliation_tag_failed | tag=%s | error=%s", name, str(e))
            errors.append(f"{name}: {e}")

    if errors:
        raise RuntimeError(
            f"Model reconciliation failed for {len(errors)} tag(s): {'; '.join(errors)}"
        )

    return archived_count
