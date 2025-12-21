# /ml_backend/logging_setup.py
import logging


def attach_file_logger(logfile_path: str, level: int = logging.DEBUG) -> None:
    """
    Attach a file handler to the root logger.

    This function is intentionally side-effecting and should be called
    exactly once during application startup.
    """
    file_handler = logging.FileHandler(logfile_path, encoding="utf-8")
    file_handler.setLevel(level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)

    logging.getLogger().addHandler(file_handler)
