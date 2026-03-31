from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.enums import GateType


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | list[Any] | None = None
    request_id: str | None = None


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
BackendProvider = Literal["aer", "ibm"]
QasmVersion = Literal["auto", "2", "3"]
OutputQasmVersion = Literal["2", "3"]
TranspileInputFormat = Literal["circuit", "qasm"]
OperationParam = float | int | bool | str


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


class CircuitDefinition(BaseModel):
    num_qubits: int = Field(ge=1)
    operations: list[CircuitOperation] = Field(min_length=1)

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

    @model_validator(mode="after")
    def validate_operation_qubit_indices(self) -> CircuitDefinition:
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


class CouplingMapSummary(BaseModel):
    present: bool
    edge_count: int = Field(ge=0)
    connected_qubit_count: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class BackendSummary(BaseModel):
    name: str
    provider: BackendProvider
    is_simulator: bool
    is_hardware: bool
    num_qubits: int = Field(ge=0)
    basis_gates: list[str]
    coupling_map_summary: CouplingMapSummary

    model_config = ConfigDict(extra="forbid")


class BackendFiltersApplied(BaseModel):
    provider: BackendProvider | None = None
    simulator_only: bool = False
    min_qubits: int = Field(default=1, ge=1)

    model_config = ConfigDict(extra="forbid")


class BackendListResponse(BaseModel):
    backends: list[BackendSummary]
    total: int = Field(ge=0)
    filters_applied: BackendFiltersApplied
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class NormalizedOperation(BaseModel):
    gate: str
    qubits: list[int] = Field(default_factory=list)
    clbits: list[int] = Field(default_factory=list)
    params: list[OperationParam] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class QasmSource(BaseModel):
    source: str = Field(min_length=1)
    qasm_version: QasmVersion = "auto"

    model_config = ConfigDict(extra="forbid")


class TranspileRequest(BaseModel):
    circuit: CircuitDefinition | None = None
    qasm: QasmSource | None = None
    backend_name: str = Field(min_length=1)
    provider: BackendProvider | None = None
    optimization_level: int = Field(default=1, ge=0, le=3)
    seed_transpiler: int | None = None
    output_qasm_version: OutputQasmVersion = "3"

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_input_source(self) -> TranspileRequest:
        if self.circuit is None and self.qasm is None:
            raise ValueError("exactly one of circuit or qasm must be provided")
        if self.circuit is not None and self.qasm is not None:
            raise ValueError("circuit and qasm are mutually exclusive")
        return self


class TranspileResponse(BaseModel):
    backend_name: str
    provider: BackendProvider
    input_format: TranspileInputFormat
    num_qubits: int = Field(ge=0)
    depth: int = Field(ge=0)
    size: int = Field(ge=0)
    operations: list[NormalizedOperation]
    qasm_version: OutputQasmVersion
    qasm: str

    model_config = ConfigDict(extra="forbid")


class QasmImportRequest(BaseModel):
    qasm: str = Field(min_length=1)
    qasm_version: QasmVersion = "auto"

    model_config = ConfigDict(extra="forbid")


class QasmImportResponse(BaseModel):
    detected_qasm_version: OutputQasmVersion
    num_qubits: int = Field(ge=0)
    depth: int = Field(ge=0)
    size: int = Field(ge=0)
    operations: list[NormalizedOperation]

    model_config = ConfigDict(extra="forbid")


class QasmExportRequest(BaseModel):
    circuit: CircuitDefinition
    qasm_version: OutputQasmVersion = "3"

    model_config = ConfigDict(extra="forbid")


class QasmExportResponse(BaseModel):
    qasm_version: OutputQasmVersion
    qasm: str
    num_qubits: int = Field(ge=0)
    depth: int = Field(ge=0)
    size: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class ApiKeyPolicyResponse(BaseModel):
    rate_limit_per_second: int = Field(ge=1)
    rate_limit_per_minute: int = Field(ge=1)
    daily_quota: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")


class ApiKeyMetadataResponse(BaseModel):
    key_id: str
    owner_user_id: str
    name: str | None = None
    key_prefix: str
    masked_key: str
    status: str
    policy: ApiKeyPolicyResponse
    created_at: datetime
    revoked_at: datetime | None = None
    rotated_from_id: str | None = None
    rotated_to_id: str | None = None
    last_used_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyMetadataResponse]

    model_config = ConfigDict(extra="forbid")


class ApiKeyCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)

    model_config = ConfigDict(extra="forbid")


class ApiKeyCreateResponse(BaseModel):
    key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyRevokeResponse(BaseModel):
    key: ApiKeyMetadataResponse

    model_config = ConfigDict(extra="forbid")


class ApiKeyRotateResponse(BaseModel):
    previous_key: ApiKeyMetadataResponse
    new_key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyDeleteResponse(BaseModel):
    deleted_key_id: str
    deleted: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiKeyDeleteRevokedResponse(BaseModel):
    deleted_count: int = Field(ge=0)

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
