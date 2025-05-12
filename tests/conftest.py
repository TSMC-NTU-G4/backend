import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
