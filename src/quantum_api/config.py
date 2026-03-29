from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def parsed_allow_origins(self) -> list[str]:
        if self.allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
