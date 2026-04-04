from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.common import ErrorResponse
from quantum_api.models.core import CircuitDefinition

BackendProvider = Literal["aer", "ibm"]
HardwareJobProvider = Literal["ibm"]
HardwareJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelling", "cancelled"]
QasmVersion = Literal["auto", "2", "3"]
OutputQasmVersion = Literal["2", "3"]
TranspileInputFormat = Literal["circuit", "qasm"]
OperationParam = float | int | bool | str


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
    ibm_profile: str | None = None

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
    ibm_profile: str | None = Field(default=None, min_length=1)
    optimization_level: int = Field(default=1, ge=0, le=3)
    seed_transpiler: int | None = None
    output_qasm_version: OutputQasmVersion = "3"

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "backend_name": "aer_simulator",
                "optimization_level": 1,
                "output_qasm_version": "3",
                "circuit": {
                    "num_qubits": 2,
                    "operations": [
                        {"gate": "h", "target": 0},
                        {"gate": "cx", "target": 1, "control": 0},
                    ],
                },
            }
        },
    )

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

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; h q[0];',
                "qasm_version": "auto",
            }
        },
    )


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

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qasm_version": "3",
                "circuit": {
                    "num_qubits": 2,
                    "operations": [
                        {"gate": "h", "target": 0},
                        {"gate": "cx", "target": 1, "control": 0},
                    ],
                },
            }
        },
    )


class QasmExportResponse(BaseModel):
    qasm_version: OutputQasmVersion
    qasm: str
    num_qubits: int = Field(ge=0)
    depth: int = Field(ge=0)
    size: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class CircuitJobSubmitRequest(BaseModel):
    provider: HardwareJobProvider = "ibm"
    backend_name: str = Field(min_length=1)
    circuit: CircuitDefinition
    shots: int = Field(default=1024, ge=1)
    ibm_profile: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "provider": "ibm",
                "backend_name": "ibm_kyiv",
                "shots": 1024,
                "ibm_profile": "IBM Open",
                "circuit": {
                    "num_qubits": 2,
                    "operations": [
                        {"gate": "h", "target": 0},
                        {"gate": "cx", "target": 1, "control": 0},
                    ],
                },
            }
        },
    )

    @field_validator("shots")
    @classmethod
    def validate_shots_limit(cls, value: int) -> int:
        max_shots = get_settings().max_circuit_shots
        if value > max_shots:
            raise ValueError(f"shots exceeds MAX_CIRCUIT_SHOTS ({max_shots})")
        return value


class CircuitJobSubmitResponse(BaseModel):
    job_id: str
    provider: HardwareJobProvider
    backend_name: str
    ibm_profile: str | None = None
    remote_job_id: str
    status: HardwareJobStatus
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class CircuitJobStatusResponse(BaseModel):
    job_id: str
    provider: HardwareJobProvider
    backend_name: str
    ibm_profile: str | None = None
    remote_job_id: str
    status: HardwareJobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error: ErrorResponse | None = None

    model_config = ConfigDict(extra="forbid")


class CircuitJobResultData(BaseModel):
    num_qubits: int = Field(ge=0)
    shots: int = Field(ge=1)
    counts: dict[str, int]

    model_config = ConfigDict(extra="forbid")


class CircuitJobResultResponse(BaseModel):
    job_id: str
    status: Literal["succeeded"] = "succeeded"
    result: CircuitJobResultData

    model_config = ConfigDict(extra="forbid")
