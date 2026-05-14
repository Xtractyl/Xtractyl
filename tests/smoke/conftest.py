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


@pytest.fixture(scope="session")
def ollama_base() -> str:
    return os.getenv("OLLAMA_BASE", "http://localhost:11434")


@pytest.fixture(scope="session")
def labelstudio_base():
    return os.getenv("LABELSTUDIO_BASE", "http://localhost:8080")


@pytest.fixture(scope="session")
def redis_host():
    return os.getenv("REDIS_HOST", "localhost")


@pytest.fixture(scope="session")
def redis_port():
    return int(os.getenv("REDIS_PORT", "6379"))


@pytest.fixture(scope="session")
def postgres_xtractyl_host():
    return os.getenv("POSTGRES_XTRACTYL_HOST", "localhost")


@pytest.fixture(scope="session")
def postgres_xtractyl_port():
    return int(os.getenv("POSTGRES_XTRACTYL_PORT", "5433"))


@pytest.fixture(scope="session")
def postgres_xtractyl_db():
    return os.getenv("POSTGRES_XTRACTYL_DB", "xtractyl")


@pytest.fixture(scope="session")
def postgres_xtractyl_user():
    return os.getenv("POSTGRES_XTRACTYL_USER", "xtractyl")


@pytest.fixture(scope="session")
def postgres_xtractyl_password():
    return os.getenv("POSTGRES_XTRACTYL_PASSWORD", "yourpassword")


@pytest.fixture(scope="session")
def minio_base():
    return os.getenv("MINIO_BASE", "http://localhost:9000")


@pytest.fixture(scope="session")
def pgadmin_base():
    return os.getenv("PGADMIN_BASE", "http://localhost:5050")
