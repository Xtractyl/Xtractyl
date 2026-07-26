# orchestrator/domain/model_reconciliation.py
import os
import time

ARCHIVE_PREFIX = os.getenv("XTRACTYL_MODEL_ARCHIVE_PREFIX", "xtractyl-archive")


def _sanitize(name: str) -> str:
    return name.replace(":", "-").replace("/", "-")


def reconcile_models(repo, ollama_client, pulled_via: str = "user_pull") -> int:
    tags = ollama_client.list_tags()
    archived_count = 0

    for entry in tags:
        name = entry.get("model") or entry.get("name")
        digest = entry.get("digest")
        if not name or not digest or name.startswith(f"{ARCHIVE_PREFIX}/"):
            continue

        existing = repo.get_by_digest(digest)
        if existing:
            repo.touch(existing.id)
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
        archived_count += 1

    return archived_count
