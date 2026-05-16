# ml_backend/utils/logging_utils.py
from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS", "0") == "1"

LOGS_DIR = pathlib.Path(os.getenv("LOGS_DIR", "/logs"))
DEV_LOGS_DIR = pathlib.Path(os.getenv("DEV_LOGS_DIR", "/app/data/logs"))

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DEV_LOGS_DIR.mkdir(parents=True, exist_ok=True)


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


safe_logger = _make_logger(
    "ml_backend.safe",
    to_stdout=True,
    file_path=LOGS_DIR / "ml_backend.safe.log",
)

dev_logger = None
if DEBUG_ARTIFACTS:
    dev_logger = _make_logger(
        "ml_backend.dev",
        to_stdout=False,
        file_path=DEV_LOGS_DIR / "ml_backend.dev.log",
    )
