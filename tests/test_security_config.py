from __future__ import annotations

import json

import pytest

from quantum_api.config import Settings
from quantum_api.security import ApiKeyAuthService

TEST_POLICY = json.dumps(
    [
        {
            "key_id": "test-key",
            "key_hash_sha256": "3700285e3c8496a57e45eb1ccd43f2424852788576961320fbb31f86f17edb61",
            "rate_limit_per_second": 10,
            "rate_limit_per_minute": 600,
            "daily_quota": 20000,
            "enabled": True,
        }
    ]
)


def test_api_key_hash_matching() -> None:
    settings = Settings(api_keys_json=TEST_POLICY)
    auth_service = ApiKeyAuthService(settings)

    principal = auth_service.authenticate("dev-local-key")
    assert principal is not None
    assert principal.key_id == "test-key"
    assert auth_service.authenticate("wrong-key") is None


def test_production_rejects_wildcard_cors() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="*",
        api_keys_json=TEST_POLICY,
        dev_rate_limit_bypass=False,
        metrics_token="metrics-secret",
    )

    with pytest.raises(ValueError, match="ALLOW_ORIGINS"):
        settings.validate_runtime_configuration()


def test_production_requires_metrics_token_when_enabled() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="https://quantum.example",
        api_keys_json=TEST_POLICY,
        dev_rate_limit_bypass=False,
        metrics_token="",
    )

    with pytest.raises(ValueError, match="METRICS_TOKEN"):
        settings.validate_runtime_configuration()
