import pytest
from fastapi.testclient import TestClient

from quantum_api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
