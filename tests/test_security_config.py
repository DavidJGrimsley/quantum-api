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


def test_total_key_limit_must_cover_active_key_limit() -> None:
    settings = Settings(
        max_active_api_keys_per_user=10,
        max_total_api_keys_per_user=9,
    )

    with pytest.raises(ValueError, match="MAX_TOTAL_API_KEYS_PER_USER"):
        settings.validate_runtime_configuration()


def test_development_injects_localhost_origins_when_allowlist_explicit() -> None:
    settings = Settings(
        app_env="development",
        allow_origins="https://davidjgrimsley.com",
    )

    origins = settings.effective_allow_origins()
    assert "https://davidjgrimsley.com" in origins
    assert "http://localhost:8081" in origins
    assert "http://127.0.0.1:8081" in origins


def test_development_localhost_injection_can_be_disabled() -> None:
    settings = Settings(
        app_env="development",
        allow_origins="https://davidjgrimsley.com",
        dev_cors_allow_localhost=False,
    )

    origins = settings.effective_allow_origins()
    assert origins == ["https://davidjgrimsley.com"]


def test_non_development_does_not_inject_localhost_origins() -> None:
    settings = Settings(
        app_env="production",
        allow_origins="https://davidjgrimsley.com",
        dev_rate_limit_bypass=False,
        metrics_token="metrics-secret",
        database_auto_create=False,
        api_key_hash_secret="prod-secret",
    )

    settings.validate_runtime_configuration()
    origins = settings.effective_allow_origins()
    assert origins == ["https://davidjgrimsley.com"]
