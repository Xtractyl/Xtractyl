# /ml_backend/utils.py
import os
import unicodedata


def origin_from_env(prefix: str, default_port: int, default_host: str = "localhost") -> str:
    origin = os.getenv(f"{prefix}_ORIGIN") or os.getenv(f"{prefix}_URL")
    if origin:
        return origin
    host = os.getenv(f"{prefix}_HOST", default_host)
    port = os.getenv(f"{prefix}_PORT", str(default_port))
    scheme = os.getenv(f"{prefix}_SCHEME", "http")
    return f"{scheme}://{host}:{port}"


# ----------------------------------
# Normalization helpers
# ----------------------------------


def norm_char(c: str) -> str:
    """
    Character-wise normalization.
    IMPORTANT: no strip() here, because we need length preservation
    for correct index mapping.
    """
    return (
        unicodedata.normalize("NFKC", c)
        .replace("\u00ad", "")  # soft hyphen
        .replace("\u00a0", " ")  # NBSP -> space
        .replace("\r", "")
        .replace("\n", "")
    )


def build_norm_index(original_text: str):
    """
    Returns (norm_text, index_map)

    norm_text: normalized concatenated string
    index_map[j]: original index of the j-th character in norm_text
    """
    norm_parts = []
    index_map = []

    for i, ch in enumerate(original_text):
        n = norm_char(ch)
        if not n:
            continue

        norm_parts.append(n)
        for _ in range(len(n)):
            index_map.append(i)

    return "".join(norm_parts), index_map


def normalize_text_block(text: str) -> str:
    """
    Block-level normalization for answers.
    strip() is OK here because offsets are NOT mapped back.
    """
    return (
        unicodedata.normalize("NFKC", text or "")
        .replace("\u00ad", "")
        .replace("\u00a0", " ")
        .replace("\r", "")
        .replace("\n", "")
        .strip()
    )
