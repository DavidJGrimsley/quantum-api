import pytest
from fastapi.testclient import TestClient

from quantum_api.main import app

TEST_API_KEY = "dev-local-key"


@pytest.fixture
def client() -> TestClient:
    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as test_client:
        yield test_client


@pytest.fixture
def unauth_client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
