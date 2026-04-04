from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.core import Amplitude, CircuitDefinition
from quantum_api.models.phase2 import NormalizedOperation
from quantum_api.models.qiskit_common import AnsatzConfig, OptimizerConfig, PauliTerm

AlgorithmProvider = Literal["qiskit-algorithms"]
AmplitudeEstimationVariant = Literal["ae", "iae", "fae", "mlae"]
PhaseEstimationVariant = Literal["standard", "iterative", "hamiltonian"]
TimeEvolutionVariant = Literal["trotter_qrte", "var_qrte", "var_qite", "pvqd"]


class GroverOracleSummary(BaseModel):
    mode: Literal["marked_bitstrings", "oracle_circuit"]
    num_qubits: int
    marked_state_count: int | None = None

    model_config = ConfigDict(extra="forbid")


class GroverSearchRequest(BaseModel):
    marked_bitstrings: list[str] | None = None
    oracle_circuit: CircuitDefinition | None = None
    good_state_bitstrings: list[str] | None = None
    state_preparation: CircuitDefinition | None = None
    objective_qubits: list[int] | None = None
    iterations: int | list[int] | None = None
    sample_from_iterations: bool = False
    shots: int = Field(default=512, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "marked_bitstrings": ["11"],
                "iterations": [1],
                "sample_from_iterations": False,
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

    @field_validator("iterations")
    @classmethod
    def validate_iterations(cls, value: int | list[int] | None) -> int | list[int] | None:
        if value is None:
            return value
        if isinstance(value, int):
            if value < 1:
                raise ValueError("iterations must be >= 1")
            return value
        if not value or any(item < 1 for item in value):
            raise ValueError("iterations list must contain positive integers")
        return value

    @field_validator("objective_qubits")
    @classmethod
    def validate_objective_qubits(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        if len(set(value)) != len(value):
            raise ValueError("objective_qubits must be unique")
        return value

    @model_validator(mode="after")
    def validate_inputs(self) -> GroverSearchRequest:
        if (self.marked_bitstrings is None) == (self.oracle_circuit is None):
            raise ValueError("exactly one of marked_bitstrings or oracle_circuit must be provided")
        if self.marked_bitstrings is not None:
            lengths = {len(item) for item in self.marked_bitstrings}
            if not self.marked_bitstrings or len(lengths) != 1:
                raise ValueError("marked_bitstrings must contain at least one equally sized bitstring")
            if any(set(item) - {"0", "1"} for item in self.marked_bitstrings):
                raise ValueError("marked_bitstrings must contain only binary strings")
        if self.good_state_bitstrings is not None:
            lengths = {len(item) for item in self.good_state_bitstrings}
            if not self.good_state_bitstrings or len(lengths) != 1:
                raise ValueError("good_state_bitstrings must contain equally sized bitstrings")
            if any(set(item) - {"0", "1"} for item in self.good_state_bitstrings):
                raise ValueError("good_state_bitstrings must contain only binary strings")
        if self.oracle_circuit is not None and not self.good_state_bitstrings:
            raise ValueError("good_state_bitstrings are required when oracle_circuit is provided")
        return self


class GroverSearchResponse(BaseModel):
    top_measurement: str
    counts: dict[str, int]
    iterations_used: list[int]
    good_state_found: bool
    oracle_summary: GroverOracleSummary
    provider: AlgorithmProvider = "qiskit-algorithms"
    backend_mode: str = "statevector_sampler"

    model_config = ConfigDict(extra="forbid")


class AmplitudeEstimationRequest(BaseModel):
    variant: AmplitudeEstimationVariant
    state_preparation: CircuitDefinition
    objective_qubits: list[int] = Field(min_length=1)
    grover_operator: CircuitDefinition | None = None
    num_eval_qubits: int | None = Field(default=None, ge=1, le=8)
    epsilon_target: float | None = Field(default=None, gt=0.0, lt=1.0)
    alpha: float | None = Field(default=None, gt=0.0, lt=1.0)
    delta: float | None = Field(default=None, gt=0.0, lt=1.0)
    maxiter: int | None = Field(default=None, ge=1, le=64)
    rescale: bool = True
    evaluation_schedule: int | list[int] | None = None
    shots: int = Field(default=512, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "variant": "ae",
                "state_preparation": {
                    "num_qubits": 1,
                    "operations": [{"gate": "ry", "target": 0, "theta": 1.2}],
                },
                "objective_qubits": [0],
                "num_eval_qubits": 2,
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

    @field_validator("objective_qubits")
    @classmethod
    def validate_objective_qubits(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("objective_qubits must be unique")
        return value

    @field_validator("evaluation_schedule")
    @classmethod
    def validate_evaluation_schedule(cls, value: int | list[int] | None) -> int | list[int] | None:
        if value is None:
            return value
        if isinstance(value, int):
            if value < 1:
                raise ValueError("evaluation_schedule must be >= 1")
            return value
        if not value or any(item < 1 for item in value):
            raise ValueError("evaluation_schedule must contain positive integers")
        return value

    @model_validator(mode="after")
    def validate_variant_requirements(self) -> AmplitudeEstimationRequest:
        qubit_count = self.state_preparation.num_qubits
        if any(index >= qubit_count for index in self.objective_qubits):
            raise ValueError("objective_qubits must be within state_preparation.num_qubits")
        if self.variant == "ae":
            if self.num_eval_qubits is None:
                raise ValueError("num_eval_qubits is required for variant 'ae'")
        elif self.variant == "iae":
            if self.epsilon_target is None or self.alpha is None:
                raise ValueError("epsilon_target and alpha are required for variant 'iae'")
        elif self.variant == "fae":
            if self.delta is None or self.maxiter is None:
                raise ValueError("delta and maxiter are required for variant 'fae'")
        elif self.variant == "mlae" and self.evaluation_schedule is None:
            raise ValueError("evaluation_schedule is required for variant 'mlae'")
        return self


class AmplitudeEstimationResponse(BaseModel):
    estimate: float
    processed_estimate: float | None = None
    confidence_interval: list[float] | None = None
    variant: AmplitudeEstimationVariant
    provider: AlgorithmProvider = "qiskit-algorithms"
    backend_mode: str = "statevector_sampler"
    raw_metadata: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class PhaseEstimationRequest(BaseModel):
    variant: PhaseEstimationVariant
    unitary: CircuitDefinition | None = None
    hamiltonian: list[PauliTerm] | None = None
    state_preparation: CircuitDefinition | None = None
    num_evaluation_qubits: int | None = Field(default=None, ge=1, le=8)
    num_iterations: int | None = Field(default=None, ge=1, le=8)
    bound: float | None = Field(default=None, gt=0.0)
    shots: int = Field(default=512, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "variant": "standard",
                "unitary": {
                    "num_qubits": 1,
                    "operations": [{"gate": "z", "target": 0}],
                },
                "state_preparation": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "num_evaluation_qubits": 3,
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

    @model_validator(mode="after")
    def validate_variant_requirements(self) -> PhaseEstimationRequest:
        if self.variant in {"standard", "iterative"}:
            if self.unitary is None:
                raise ValueError("unitary is required for standard and iterative phase estimation")
            if self.hamiltonian is not None:
                raise ValueError("hamiltonian is only valid for variant 'hamiltonian'")
        if self.variant == "standard":
            if self.num_evaluation_qubits is None:
                raise ValueError("num_evaluation_qubits is required for variant 'standard'")
            if self.num_iterations is not None:
                raise ValueError("num_iterations is only valid for variant 'iterative'")
        elif self.variant == "iterative":
            if self.num_iterations is None:
                raise ValueError("num_iterations is required for variant 'iterative'")
            if self.num_evaluation_qubits is not None:
                raise ValueError("num_evaluation_qubits is only valid for variants 'standard' and 'hamiltonian'")
        else:
            if self.hamiltonian is None:
                raise ValueError("hamiltonian is required for variant 'hamiltonian'")
            if self.num_evaluation_qubits is None:
                raise ValueError("num_evaluation_qubits is required for variant 'hamiltonian'")
            if self.unitary is not None:
                raise ValueError("unitary is only valid for variants 'standard' and 'iterative'")
        return self


class PhaseEstimationResponse(BaseModel):
    most_likely_phase: float
    phase_distribution: dict[str, float] | None = None
    estimated_eigenvalue: float | None = None
    variant: PhaseEstimationVariant
    provider: AlgorithmProvider = "qiskit-algorithms"
    backend_mode: str = "statevector_sampler"

    model_config = ConfigDict(extra="forbid")


class NamedPauliSum(BaseModel):
    name: str = Field(min_length=1)
    pauli_sum: list[PauliTerm] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class TimeEvolutionAuxOperatorValue(BaseModel):
    name: str
    value: Amplitude
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class TimeEvolutionRequest(BaseModel):
    variant: TimeEvolutionVariant
    hamiltonian: list[PauliTerm] = Field(min_length=1)
    time: float = Field(gt=0.0)
    initial_state: CircuitDefinition | None = None
    aux_operators: list[NamedPauliSum] | None = None
    num_timesteps: int | None = Field(default=None, ge=1, le=32)
    ansatz: AnsatzConfig | None = None
    initial_parameters: list[float] | None = None
    optimizer: OptimizerConfig | None = None
    shots: int = Field(default=512, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "variant": "trotter_qrte",
                "hamiltonian": [{"pauli": "Z", "coefficient": 1.0}],
                "time": 0.5,
                "initial_state": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "num_timesteps": 2,
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

    @model_validator(mode="after")
    def validate_variant_requirements(self) -> TimeEvolutionRequest:
        if self.variant == "trotter_qrte":
            if self.initial_state is None:
                raise ValueError("initial_state is required for variant 'trotter_qrte'")
            if self.ansatz is not None or self.initial_parameters is not None or self.optimizer is not None:
                raise ValueError("ansatz, initial_parameters, and optimizer are not used by variant 'trotter_qrte'")
        elif self.variant in {"var_qrte", "var_qite"}:
            if self.ansatz is None or self.initial_parameters is None:
                raise ValueError("ansatz and initial_parameters are required for variational time evolution")
            if self.initial_state is not None:
                raise ValueError("initial_state is not supported for variational time evolution variants")
            if self.optimizer is not None:
                raise ValueError("optimizer is only valid for variant 'pvqd'")
        else:
            if self.ansatz is None or self.initial_parameters is None or self.optimizer is None:
                raise ValueError("ansatz, initial_parameters, and optimizer are required for variant 'pvqd'")
            if self.initial_state is not None:
                raise ValueError("initial_state is not supported for variant 'pvqd'")
        return self


class TimeEvolutionResponse(BaseModel):
    final_state_operations: list[NormalizedOperation]
    final_statevector: list[Amplitude]
    times: list[float] | None = None
    aux_operator_values: list[TimeEvolutionAuxOperatorValue] | None = None
    final_parameters: list[float] | None = None
    fidelities: list[float] | None = None
    variant: TimeEvolutionVariant
    provider: AlgorithmProvider = "qiskit-algorithms"
    backend_mode: str
    raw_metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")
