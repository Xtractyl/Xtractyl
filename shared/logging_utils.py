# shared/logging_utils.py
from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS", "0") == "1"
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown")

LOGS_DIR = pathlib.Path(os.getenv("LOGS_DIR", "/logs"))
DEV_LOGS_DIR = pathlib.Path(os.getenv("DEV_LOGS_DIR", "/app/data/logs"))

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DEV_LOGS_DIR.mkdir(parents=True, exist_ok=True)


class SafeLogger(logging.Logger):
    def exception(self, msg, *args, **kwargs):
        kwargs.pop("exc_info", None)
        self.error(msg, *args, **kwargs)


def _make_logger(
    name: str,
    *,
    safe: bool = False,
    level: int = logging.INFO,
    to_stdout: bool = False,
    file_path: Optional[pathlib.Path] = None,
) -> logging.Logger:
    if safe:
        logging.setLoggerClass(SafeLogger)
    logger = logging.getLogger(name)
    logging.setLoggerClass(logging.Logger)
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
    f"{SERVICE_NAME}.safe",
    safe=True,
    to_stdout=True,
    file_path=LOGS_DIR / f"{SERVICE_NAME}.safe.log",
)

dev_logger = None
if DEBUG_ARTIFACTS:
    dev_logger = _make_logger(
        f"{SERVICE_NAME}.dev",
        to_stdout=False,
        file_path=DEV_LOGS_DIR / f"{SERVICE_NAME}.dev.log",
    )
