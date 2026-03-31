from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_HASH_SECRET = "dev-only-change-me"


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
    dev_cors_allow_localhost: bool = Field(default=True, alias="DEV_CORS_ALLOW_LOCALHOST")
    dev_cors_local_origins: str = Field(
        default="http://localhost:8081,http://127.0.0.1:8081,http://localhost:3000,http://127.0.0.1:3000,http://localhost:19006,http://127.0.0.1:19006",
        alias="DEV_CORS_LOCAL_ORIGINS",
    )
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
    api_key_hash_secret: str = Field(default=_DEFAULT_HASH_SECRET, alias="API_KEY_HASH_SECRET")
    api_key_format_prefix: str = Field(default="qapi", alias="API_KEY_FORMAT_PREFIX")
    api_key_prefix_length: int = Field(default=12, alias="API_KEY_PREFIX_LENGTH", ge=6, le=24)
    api_key_secret_length: int = Field(default=40, alias="API_KEY_SECRET_LENGTH", ge=16, le=128)
    api_key_cache_ttl_seconds: int = Field(default=90, alias="API_KEY_CACHE_TTL_SECONDS", ge=5, le=86400)

    default_key_rate_limit_per_second: int = Field(
        default=10,
        alias="DEFAULT_KEY_RATE_LIMIT_PER_SECOND",
        ge=1,
        le=100000,
    )
    default_key_rate_limit_per_minute: int = Field(
        default=600,
        alias="DEFAULT_KEY_RATE_LIMIT_PER_MINUTE",
        ge=1,
        le=1000000,
    )
    default_key_daily_quota: int = Field(
        default=20000,
        alias="DEFAULT_KEY_DAILY_QUOTA",
        ge=1,
        le=1000000000,
    )
    max_active_api_keys_per_user: int = Field(
        default=5,
        alias="MAX_ACTIVE_API_KEYS_PER_USER",
        ge=1,
        le=1000,
    )
    max_total_api_keys_per_user: int = Field(
        default=100,
        alias="MAX_TOTAL_API_KEYS_PER_USER",
        ge=1,
        le=10000,
    )

    database_url: str = Field(default="sqlite+aiosqlite:///./quantum_api.db", alias="DATABASE_URL")
    database_auto_create: bool = Field(default=True, alias="DATABASE_AUTO_CREATE")

    supabase_url: str = Field(default="https://example.supabase.co", alias="SUPABASE_URL")
    supabase_jwt_audience: str = Field(default="authenticated", alias="SUPABASE_JWT_AUDIENCE")
    supabase_jwt_issuer: str = Field(default="", alias="SUPABASE_JWT_ISSUER")
    supabase_jwks_cache_seconds: int = Field(
        default=300,
        alias="SUPABASE_JWKS_CACHE_SECONDS",
        ge=15,
        le=3600,
    )

    dev_bootstrap_api_key_enabled: bool = Field(default=True, alias="DEV_BOOTSTRAP_API_KEY_ENABLED")
    dev_bootstrap_api_key: str = Field(
        default="qapi_devlocal_0123456789abcdef0123456789abcdef",
        alias="DEV_BOOTSTRAP_API_KEY",
    )
    dev_bootstrap_owner_id: str = Field(default="local-dev", alias="DEV_BOOTSTRAP_OWNER_ID")

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

    def parsed_dev_cors_local_origins(self) -> list[str]:
        return [origin.strip() for origin in self.dev_cors_local_origins.split(",") if origin.strip()]

    def effective_allow_origins(self) -> list[str]:
        origins = self.parsed_allow_origins()
        if self.app_env_normalized != "development":
            return origins
        if not self.dev_cors_allow_localhost:
            return origins
        if "*" in origins:
            return origins

        merged: list[str] = []
        seen: set[str] = set()
        for origin in [*origins, *self.parsed_dev_cors_local_origins()]:
            if origin not in seen:
                seen.add(origin)
                merged.append(origin)
        return merged

    def requires_api_key(self, path: str) -> bool:
        prefix = self.api_prefix.rstrip("/")
        if not path.startswith(prefix):
            return False
        if path == f"{prefix}/health":
            return False
        return not path.startswith(f"{prefix}/keys")

    def requires_user_jwt(self, path: str) -> bool:
        prefix = self.api_prefix.rstrip("/")
        return path.startswith(f"{prefix}/keys")

    @property
    def supabase_jwt_issuer_effective(self) -> str:
        explicit = self.supabase_jwt_issuer.strip()
        if explicit:
            return explicit
        if not self.supabase_url.strip():
            return ""
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    def validate_runtime_configuration(self) -> None:
        if self.ip_rate_limit_per_minute < self.ip_rate_limit_per_second:
            raise ValueError("IP_RATE_LIMIT_PER_MINUTE must be >= IP_RATE_LIMIT_PER_SECOND")
        if self.default_key_rate_limit_per_minute < self.default_key_rate_limit_per_second:
            raise ValueError(
                "DEFAULT_KEY_RATE_LIMIT_PER_MINUTE must be >= DEFAULT_KEY_RATE_LIMIT_PER_SECOND"
            )
        if self.max_total_api_keys_per_user < self.max_active_api_keys_per_user:
            raise ValueError("MAX_TOTAL_API_KEYS_PER_USER must be >= MAX_ACTIVE_API_KEYS_PER_USER")

        if self.is_production_like():
            origins = self.parsed_allow_origins()
            if not origins or "*" in origins:
                raise ValueError("ALLOW_ORIGINS must be an explicit allowlist in staging/production")
            if self.dev_rate_limit_bypass:
                raise ValueError("DEV_RATE_LIMIT_BYPASS must be false in staging/production")
            if self.database_auto_create:
                raise ValueError("DATABASE_AUTO_CREATE must be false in staging/production")
            if self.api_key_hash_secret.strip() == _DEFAULT_HASH_SECRET:
                raise ValueError("API_KEY_HASH_SECRET must be changed in staging/production")

        if self.auth_enabled:
            if not self.database_url.strip():
                raise ValueError("AUTH_ENABLED=true requires DATABASE_URL")
            if not self.api_key_hash_secret.strip():
                raise ValueError("AUTH_ENABLED=true requires API_KEY_HASH_SECRET")
            if not self.supabase_url.strip():
                raise ValueError("AUTH_ENABLED=true requires SUPABASE_URL")
            if not self.supabase_jwt_audience.strip():
                raise ValueError("AUTH_ENABLED=true requires SUPABASE_JWT_AUDIENCE")
            if not self.supabase_jwt_issuer_effective.strip():
                raise ValueError("AUTH_ENABLED=true requires SUPABASE_JWT_ISSUER or SUPABASE_URL")

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
