# orchestrator/utils/hashing.py
import hashlib

# we are currently ignoring order in questions and labels hashes, because order is arbitrary
# we should think about a questions_and_labels_hash to check for matching order later
# currently this remains for the user to guarantee


def compute_labels_hash(labels: list[str]) -> str:
    normalized = sorted(label.strip() for label in labels)
    joined = "|".join(normalized)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def compute_questions_hash(questions: list[str]) -> str:
    normalized = sorted(q.strip() for q in (questions or []))
    joined = "|".join(normalized)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def compute_document_set_hash(html_hashes) -> str:
    # Aggregate hash over a whole document set so two evaluations can be
    # compared with a single string equality instead of a full set diff.
    normalized = sorted(h for h in (html_hashes or []) if h)
    joined = "|".join(normalized)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def compute_system_prompt_hash(system_prompt: str | None) -> str:
    # Unlike the two helpers above, this hashes a single string, not a
    # list — long prompts would otherwise force matching to compare a
    # potentially large text column instead of a fixed-length hash.
    normalized = (system_prompt or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
