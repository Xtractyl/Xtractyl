# tests/smoke/conftest.py
import os

import pytest


@pytest.fixture(scope="session")
def orch_base():
    return os.getenv("ORCH_BASE", "http://localhost:5001")


@pytest.fixture(scope="session")
def frontend_base():
    return os.getenv("FRONTEND_BASE", "http://localhost:5173")


@pytest.fixture(scope="session")
def ml_backend_base():
    return os.getenv("ML_BACKEND_BASE", "http://localhost:6789")
