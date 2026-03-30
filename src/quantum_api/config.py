from __future__ import annotations

import json
import re
from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")

_DEFAULT_API_KEYS_JSON = json.dumps(
    [
        {
            "key_id": "dev-local",
            "key_hash_sha256": "3700285e3c8496a57e45eb1ccd43f2424852788576961320fbb31f86f17edb61",
            "rate_limit_per_second": 10,
            "rate_limit_per_minute": 600,
            "daily_quota": 20000,
            "enabled": True,
        }
    ]
)


class ApiKeyPolicy(BaseModel):
    key_id: str = Field(min_length=1)
    key_hash_sha256: str = Field(min_length=64, max_length=64)
    rate_limit_per_second: int = Field(ge=1, le=100000)
    rate_limit_per_minute: int = Field(ge=1, le=1000000)
    daily_quota: int = Field(ge=1, le=1000000000)
    enabled: bool = True

    @field_validator("key_hash_sha256")
    @classmethod
    def validate_hash_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _SHA256_HEX_PATTERN.fullmatch(normalized):
            raise ValueError("key_hash_sha256 must be a lowercase SHA-256 hex string")
        return normalized

    @field_validator("rate_limit_per_minute")
    @classmethod
    def validate_per_minute_not_below_second(cls, value: int, info) -> int:
        per_second = info.data.get("rate_limit_per_second")
        if isinstance(per_second, int) and value < per_second:
            raise ValueError("rate_limit_per_minute must be >= rate_limit_per_second")
        return value


class Settings(BaseSettings):
    app_name: str = "Quantum API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/v1", alias="API_PREFIX")
    max_text_length: int = Field(default=2000, alias="MAX_TEXT_LENGTH", ge=1, le=20000)
    max_circuit_qubits: int = Field(default=8, alias="MAX_CIRCUIT_QUBITS", ge=1, le=32)
    max_circuit_depth: int = Field(default=256, alias="MAX_CIRCUIT_DEPTH", ge=1, le=10000)
    max_circuit_shots: int = Field(default=4096, alias="MAX_CIRCUIT_SHOTS", ge=1, le=100000)
    allow_origins: str = Field(default="*", alias="ALLOW_ORIGINS")
    request_timeout_seconds: float = Field(
        default=5.0,
        alias="REQUEST_TIMEOUT_SECONDS",
        ge=0.5,
        le=30.0,
    )
    require_qiskit: bool = Field(default=False, alias="REQUIRE_QISKIT")
    ibm_token: str = Field(default="", alias="IBM_TOKEN")
    ibm_instance: str = Field(default="", alias="IBM_INSTANCE")
    ibm_channel: str = Field(default="ibm_quantum", alias="IBM_CHANNEL")

    auth_enabled: bool = Field(default=True, alias="AUTH_ENABLED")
    api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")
    api_keys_json: str = Field(default=_DEFAULT_API_KEYS_JSON, alias="API_KEYS_JSON")

    rate_limiting_enabled: bool = Field(default=True, alias="RATE_LIMITING_ENABLED")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")
    dev_rate_limit_bypass: bool = Field(default=True, alias="DEV_RATE_LIMIT_BYPASS")
    ip_rate_limit_per_second: int = Field(default=20, alias="IP_RATE_LIMIT_PER_SECOND", ge=1, le=100000)
    ip_rate_limit_per_minute: int = Field(default=900, alias="IP_RATE_LIMIT_PER_MINUTE", ge=1, le=1000000)

    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_path: str = Field(default="/metrics", alias="METRICS_PATH")
    metrics_token: str = Field(default="", alias="METRICS_TOKEN")
    metrics_token_header: str = Field(default="X-Metrics-Token", alias="METRICS_TOKEN_HEADER")

    request_id_header: str = Field(default="X-Request-ID", alias="REQUEST_ID_HEADER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def app_env_normalized(self) -> str:
        return self.app_env.strip().lower()

    def is_production_like(self) -> bool:
        return self.app_env_normalized in {"staging", "production"}

    def parsed_allow_origins(self) -> list[str]:
        if self.allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allow_origins.split(",") if origin.strip()]

    def parsed_api_keys(self) -> list[ApiKeyPolicy]:
        raw = self.api_keys_json.strip()
        if not raw:
            return []

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("API_KEYS_JSON must be valid JSON") from exc

        if not isinstance(decoded, list):
            raise ValueError("API_KEYS_JSON must decode to a JSON array")

        try:
            return [ApiKeyPolicy.model_validate(item) for item in decoded]
        except ValidationError as exc:
            raise ValueError("API_KEYS_JSON contains invalid policy records") from exc

    def requires_api_key(self, path: str) -> bool:
        prefix = self.api_prefix.rstrip("/")
        if not path.startswith(prefix):
            return False
        return path != f"{prefix}/health"

    def validate_runtime_configuration(self) -> None:
        if self.ip_rate_limit_per_minute < self.ip_rate_limit_per_second:
            raise ValueError("IP_RATE_LIMIT_PER_MINUTE must be >= IP_RATE_LIMIT_PER_SECOND")

        if self.is_production_like():
            origins = self.parsed_allow_origins()
            if not origins or "*" in origins:
                raise ValueError("ALLOW_ORIGINS must be an explicit allowlist in staging/production")
            if self.dev_rate_limit_bypass:
                raise ValueError("DEV_RATE_LIMIT_BYPASS must be false in staging/production")

        if self.auth_enabled:
            enabled_keys = [policy for policy in self.parsed_api_keys() if policy.enabled]
            if not enabled_keys:
                raise ValueError("AUTH_ENABLED=true requires at least one enabled key in API_KEYS_JSON")

        if self.rate_limiting_enabled and self.is_production_like() and not self.redis_url.strip():
            raise ValueError("REDIS_URL is required when RATE_LIMITING_ENABLED=true in staging/production")

        if self.metrics_enabled and self.is_production_like() and not self.metrics_token.strip():
            raise ValueError("METRICS_TOKEN is required in staging/production when metrics are enabled")

    def ibm_is_configured(self) -> bool:
        return bool(self.ibm_token.strip() and self.ibm_instance.strip())


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime_configuration()
    return settings
