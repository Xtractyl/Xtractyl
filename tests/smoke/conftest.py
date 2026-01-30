import os

import pytest


@pytest.fixture(scope="session")
def orch_base():
    return os.getenv("ORCH_BASE", "http://localhost:5001")
