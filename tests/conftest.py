import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_TEST_DB = Path(__file__).resolve().parent / "test_quantum_api.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}")
os.environ.setdefault("DATABASE_AUTO_CREATE", "true")
os.environ.setdefault("DEV_BOOTSTRAP_API_KEY_ENABLED", "true")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_JWT_AUDIENCE", "authenticated")

from quantum_api.main import app  # noqa: E402

TEST_API_KEY = "qapi_devlocal_0123456789abcdef0123456789abcdef"


@pytest.fixture
def client() -> TestClient:
    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as test_client:
        yield test_client


@pytest.fixture
def unauth_client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
