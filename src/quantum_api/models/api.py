from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.enums import GateType


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    qiskit_available: bool
    runtime_mode: str


class EchoTypeInfo(BaseModel):
    name: str
    description: str


class EchoTypesResponse(BaseModel):
    echo_types: list[EchoTypeInfo]


class GateRunRequest(BaseModel):
    gate_type: GateType
    rotation_angle_rad: float | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_rotation_rules(self) -> GateRunRequest:
        if self.gate_type == GateType.ROTATION and self.rotation_angle_rad is None:
            raise ValueError("rotation_angle_rad is required when gate_type is 'rotation'")
        if self.gate_type != GateType.ROTATION and self.rotation_angle_rad is not None:
            raise ValueError("rotation_angle_rad is only valid when gate_type is 'rotation'")
        return self


class GateRunResponse(BaseModel):
    gate_type: str
    measurement: int
    superposition_strength: float
    success: bool


class TextTransformRequest(BaseModel):
    text: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, value: str) -> str:
        max_length = get_settings().max_text_length
        if len(value) > max_length:
            raise ValueError(f"text exceeds MAX_TEXT_LENGTH ({max_length})")
        return value


class TextTransformResponse(BaseModel):
    original: str
    transformed: str
    coverage_percent: float
    quantum_words: int
    total_words: int
    category_counts: dict[str, int]
