# /ml_backend/utils.py
import os

def origin_from_env(prefix: str, default_port: int, default_host: str = "localhost") -> str:
    origin = os.getenv(f"{prefix}_ORIGIN") or os.getenv(f"{prefix}_URL")
    if origin:
        return origin
    host = os.getenv(f"{prefix}_HOST", default_host)
    port = os.getenv(f"{prefix}_PORT", str(default_port))
    scheme = os.getenv(f"{prefix}_SCHEME", "http")
    return f"{scheme}://{host}:{port}"
