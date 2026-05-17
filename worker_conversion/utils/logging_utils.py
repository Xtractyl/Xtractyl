# worker_conversion/utils/logging_utils.py

import logging
import os

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS") == "1"


def _make_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


safe_logger = _make_logger("worker_conversion.safe")
dev_logger = _make_logger("worker_conversion.dev") if DEBUG_ARTIFACTS else None
