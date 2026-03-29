from __future__ import annotations

from typing import Literal

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


class Amplitude(BaseModel):
    real: float
    imag: float

    model_config = ConfigDict(extra="forbid")


CircuitGate = Literal["x", "z", "h", "ry", "cx"]


class CircuitOperation(BaseModel):
    gate: CircuitGate
    target: int = Field(ge=0)
    theta: float | None = None
    control: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_gate_parameters(self) -> CircuitOperation:
        if self.gate == "ry" and self.theta is None:
            raise ValueError("theta is required when gate is 'ry'")
        if self.gate != "ry" and self.theta is not None:
            raise ValueError("theta is only valid when gate is 'ry'")
        if self.gate == "cx":
            if self.control is None:
                raise ValueError("control is required when gate is 'cx'")
            if self.control == self.target:
                raise ValueError("control and target must be different for 'cx'")
        elif self.control is not None:
            raise ValueError("control is only valid when gate is 'cx'")
        return self


class CircuitRunRequest(BaseModel):
    num_qubits: int = Field(ge=1)
    operations: list[CircuitOperation] = Field(min_length=1)
    shots: int = Field(default=1024, ge=1)
    include_statevector: bool = False
    seed: int | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("num_qubits")
    @classmethod
    def validate_num_qubits_limit(cls, value: int) -> int:
        max_qubits = get_settings().max_circuit_qubits
        if value > max_qubits:
            raise ValueError(f"num_qubits exceeds MAX_CIRCUIT_QUBITS ({max_qubits})")
        return value

    @field_validator("operations")
    @classmethod
    def validate_circuit_depth_limit(cls, value: list[CircuitOperation]) -> list[CircuitOperation]:
        max_depth = get_settings().max_circuit_depth
        if len(value) > max_depth:
            raise ValueError(f"operations exceeds MAX_CIRCUIT_DEPTH ({max_depth})")
        return value

    @field_validator("shots")
    @classmethod
    def validate_shots_limit(cls, value: int) -> int:
        max_shots = get_settings().max_circuit_shots
        if value > max_shots:
            raise ValueError(f"shots exceeds MAX_CIRCUIT_SHOTS ({max_shots})")
        return value

    @model_validator(mode="after")
    def validate_operation_qubit_indices(self) -> CircuitRunRequest:
        for index, operation in enumerate(self.operations):
            if operation.target >= self.num_qubits:
                raise ValueError(
                    f"operations[{index}].target={operation.target} is out of range for num_qubits={self.num_qubits}"
                )
            if operation.control is not None and operation.control >= self.num_qubits:
                raise ValueError(
                    f"operations[{index}].control={operation.control} is out of range for num_qubits={self.num_qubits}"
                )
        return self


class CircuitRunResponse(BaseModel):
    num_qubits: int
    shots: int
    counts: dict[str, int]
    backend_mode: Literal["qiskit"] = "qiskit"
    statevector: list[Amplitude] | None = None

    model_config = ConfigDict(extra="forbid")


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
