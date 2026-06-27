# orchestrator/utils/hashing.py
import hashlib


def compute_labels_hash(labels: list[str]) -> str:
    normalized = sorted(label.strip() for label in labels)
    joined = "|".join(normalized)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
