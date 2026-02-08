# orchestrator/utils/logging_utils.py
from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS", "0") == "1"

LOGS_DIR = pathlib.Path(os.getenv("LOGS_DIR", "/logs"))
DEV_LOGS_DIR = pathlib.Path(os.getenv("DEV_LOGS_DIR", "/app/data/logs"))

SAFE_LOG_DIR = LOGS_DIR
SAFE_LOG_DIR.mkdir(parents=True, exist_ok=True)

DEV_LOG_DIR = DEV_LOGS_DIR
DEV_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Fixture capture (for tests only)
FIXTURES_DIR = pathlib.Path(os.getenv("FIXTURES_DIR", "/app/data/fixtures"))
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

CAPTURE_FIXTURES = os.getenv("CAPTURE_FIXTURES", "0") == "1"
SYNTHETIC_DATA = os.getenv("SYNTHETIC_DATA", "0") == "1"


def _make_logger(
    name: str,
    *,
    level: int = logging.INFO,
    to_stdout: bool = False,
    file_path: Optional[pathlib.Path] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    if to_stdout:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    if file_path is not None:
        fh = logging.FileHandler(file_path)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# Safe logs: always on, stdout + file
safe_logger = _make_logger(
    "orchestrator.safe",
    to_stdout=True,
    file_path=SAFE_LOG_DIR / "orchestrator.safe.log",
)

# Dev logs: only file, only if DEBUG_ARTIFACTS=1
dev_logger = None
if DEBUG_ARTIFACTS:
    dev_logger = _make_logger(
        "orchestrator.dev",
        to_stdout=False,
        file_path=DEV_LOG_DIR / "orchestrator.dev.log",
    )


def write_fixture(filename: str, data: str | bytes) -> pathlib.Path | None:
    """
    Persist fixture data for later use in tests.
    Only writes when:
      DEBUG_ARTIFACTS=1 AND CAPTURE_FIXTURES=1 AND SYNTHETIC_DATA=1
    """
    if not (DEBUG_ARTIFACTS and CAPTURE_FIXTURES and SYNTHETIC_DATA):
        return None

    path = FIXTURES_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data)

    return path
