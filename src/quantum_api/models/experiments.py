from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.core import Amplitude, CircuitDefinition
from quantum_api.models.qiskit_common import QiskitDomainProvider


class DensityMatrixRow(BaseModel):
    amplitudes: list[Amplitude]

    model_config = ConfigDict(extra="forbid")


class PositivitySummary(BaseModel):
    positive: bool
    rescaled_psd: bool | None = None
    eigenvalues: list[float] = Field(default_factory=list)
    raw_eigenvalues: list[float] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class StateTomographyRequest(BaseModel):
    circuit: CircuitDefinition
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None
    target_statevector: list[Amplitude] | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "circuit": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "shots": 512,
                "seed": 7,
                "target_statevector": [
                    {"real": 0.70710678, "imag": 0.0},
                    {"real": 0.70710678, "imag": 0.0},
                ],
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

    @model_validator(mode="after")
    def validate_target_length(self) -> StateTomographyRequest:
        if self.target_statevector is not None:
            expected = 2 ** self.circuit.num_qubits
            if len(self.target_statevector) != expected:
                raise ValueError("target_statevector length must equal 2 ** circuit.num_qubits")
        return self


class StateTomographyResponse(BaseModel):
    reconstructed_density_matrix: list[DensityMatrixRow]
    trace: float
    positivity: PositivitySummary
    state_fidelity: float | None = None
    provider: QiskitDomainProvider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")


class RandomizedBenchmarkingRequest(BaseModel):
    qubits: list[int] = Field(min_length=1, max_length=4)
    sequence_lengths: list[int] = Field(min_length=2, max_length=8)
    num_samples: int = Field(default=3, ge=1, le=16)
    shots: int = Field(default=512, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qubits": [0],
                "sequence_lengths": [1, 2, 4, 8],
                "num_samples": 3,
                "shots": 256,
                "seed": 7,
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

    @field_validator("sequence_lengths")
    @classmethod
    def validate_sequence_lengths(cls, value: list[int]) -> list[int]:
        if any(item <= 0 for item in value):
            raise ValueError("sequence_lengths must be positive integers")
        if sorted(value) != value:
            raise ValueError("sequence_lengths must be sorted ascending")
        return value

    @field_validator("qubits")
    @classmethod
    def validate_qubits(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("qubits must be unique")
        return value


class RandomizedBenchmarkingResponse(BaseModel):
    alpha: float
    epc: float
    fit_metrics: dict[str, float | None]
    provider: QiskitDomainProvider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")


class QuantumVolumeRequest(BaseModel):
    qubits: list[int] = Field(min_length=2, max_length=4)
    trials: int = Field(default=5, ge=3, le=20)
    shots: int = Field(default=256, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qubits": [0, 1],
                "trials": 5,
                "shots": 128,
                "seed": 7,
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

    @field_validator("qubits")
    @classmethod
    def validate_qubits(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("qubits must be unique")
        return value


class QuantumVolumeResponse(BaseModel):
    quantum_volume: int
    mean_heavy_output_probability: float | None = None
    analysis_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")


class T1ExperimentRequest(BaseModel):
    qubits: list[int] = Field(min_length=1, max_length=1)
    delays: list[float] = Field(min_length=4, max_length=16)
    shots: int = Field(default=256, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qubits": [0],
                "delays": [0.000001, 0.000002, 0.000003, 0.000004],
                "shots": 128,
                "seed": 7,
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

    @field_validator("delays")
    @classmethod
    def validate_delays(cls, value: list[float]) -> list[float]:
        if any(item <= 0 for item in value):
            raise ValueError("delays must be positive")
        if sorted(value) != value:
            raise ValueError("delays must be sorted ascending")
        return value


class T1ExperimentResponse(BaseModel):
    t1_seconds: float
    fit_metrics: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")


class T2RamseyExperimentRequest(BaseModel):
    qubits: list[int] = Field(min_length=1, max_length=1)
    delays: list[float] = Field(min_length=5, max_length=16)
    osc_freq: float = Field(default=100000.0, ge=0.0)
    shots: int = Field(default=256, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "qubits": [0],
                "delays": [0.000001, 0.000002, 0.000003, 0.000004, 0.000005],
                "osc_freq": 100000.0,
                "shots": 128,
                "seed": 7,
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

    @field_validator("delays")
    @classmethod
    def validate_delays(cls, value: list[float]) -> list[float]:
        if any(item <= 0 for item in value):
            raise ValueError("delays must be positive")
        if sorted(value) != value:
            raise ValueError("delays must be sorted ascending")
        return value


class T2RamseyExperimentResponse(BaseModel):
    t2star_seconds: float
    oscillation_frequency_hz: float | None = None
    fit_metrics: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")
