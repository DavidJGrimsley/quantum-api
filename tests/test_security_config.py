from __future__ import annotations

import pytest

from quantum_api.config import Settings


def test_production_rejects_wildcard_cors() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="*",
        dev_rate_limit_bypass=False,
        metrics_token="metrics-secret",
        database_auto_create=False,
        api_key_hash_secret="prod-secret",
    )

    with pytest.raises(ValueError, match="ALLOW_ORIGINS"):
        settings.validate_runtime_configuration()


def test_production_requires_metrics_token_when_enabled() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="https://quantum.example",
        dev_rate_limit_bypass=False,
        metrics_token="",
        database_auto_create=False,
        api_key_hash_secret="prod-secret",
    )

    with pytest.raises(ValueError, match="METRICS_TOKEN"):
        settings.validate_runtime_configuration()


def test_production_rejects_default_hash_secret() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="https://quantum.example",
        dev_rate_limit_bypass=False,
        metrics_token="metrics-secret",
        database_auto_create=False,
        api_key_hash_secret="dev-only-change-me",
    )

    with pytest.raises(ValueError, match="API_KEY_HASH_SECRET"):
        settings.validate_runtime_configuration()


def test_default_key_rate_limit_minute_must_cover_second() -> None:
    settings = Settings(
        default_key_rate_limit_per_second=100,
        default_key_rate_limit_per_minute=99,
    )

    with pytest.raises(ValueError, match="DEFAULT_KEY_RATE_LIMIT_PER_MINUTE"):
        settings.validate_runtime_configuration()
