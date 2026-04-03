from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.core import Amplitude, CircuitDefinition

Phase5Provider = Literal[
    "qiskit-algorithms",
    "qiskit-experiments",
    "qiskit-finance",
    "qiskit-machine-learning",
    "qiskit-nature",
]


class Phase5OptimizerConfig(BaseModel):
    name: Literal["cobyla", "slsqp", "spsa"] = "cobyla"
    maxiter: int = Field(default=100, ge=1, le=500)
    tol: float | None = Field(default=None, gt=0.0)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "cobyla", "maxiter": 50, "tol": 0.001}},
    )


class Phase5OptimizerMetadata(BaseModel):
    name: str
    maxiter: int
    evaluations: int | None = None
    optimizer_time_seconds: float | None = None

    model_config = ConfigDict(extra="forbid")


class BinaryQuadraticTerm(BaseModel):
    i: int = Field(ge=0)
    j: int = Field(ge=0)
    value: float

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_order(self) -> BinaryQuadraticTerm:
        if self.i > self.j:
            raise ValueError("quadratic term indices must be ordered so i <= j")
        return self


class BinaryQuadraticProblem(BaseModel):
    num_variables: int = Field(ge=1, le=16)
    linear: list[float]
    quadratic: list[BinaryQuadraticTerm] = Field(default_factory=list)
    constant: float = 0.0
    sense: Literal["minimize", "maximize"] = "minimize"
    variable_names: list[str] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("linear")
    @classmethod
    def validate_linear_length(cls, value: list[float]) -> list[float]:
        if not value:
            raise ValueError("linear must contain at least one coefficient")
        return value

    @model_validator(mode="after")
    def validate_lengths(self) -> BinaryQuadraticProblem:
        if len(self.linear) != self.num_variables:
            raise ValueError("linear coefficient count must equal num_variables")
        if self.variable_names is not None and len(self.variable_names) != self.num_variables:
            raise ValueError("variable_names count must equal num_variables")
        for term in self.quadratic:
            if term.i >= self.num_variables or term.j >= self.num_variables:
                raise ValueError("quadratic term indices must be within num_variables")
        return self


class OptimizationSolutionSample(BaseModel):
    bitstring: str
    objective_value: float
    probability: float = Field(ge=0.0)
    status: str

    model_config = ConfigDict(extra="forbid")


class OptimizationQaoaRequest(BaseModel):
    problem: BinaryQuadraticProblem
    reps: int = Field(default=1, ge=1, le=4)
    optimizer: Phase5OptimizerConfig = Field(default_factory=Phase5OptimizerConfig)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "problem": {
                    "num_variables": 2,
                    "linear": [1.0, -2.0],
                    "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
                    "sense": "minimize",
                },
                "reps": 1,
                "optimizer": {"name": "cobyla", "maxiter": 25},
                "shots": 512,
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


class OptimizationQaoaResponse(BaseModel):
    best_bitstring: str
    objective_value: float
    solution_samples: list[OptimizationSolutionSample]
    optimizer_metadata: Phase5OptimizerMetadata
    provider: Phase5Provider = "qiskit-algorithms"
    backend_mode: str = "statevector_sampler"
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class PauliTerm(BaseModel):
    pauli: str = Field(min_length=1)
    coefficient: float

    model_config = ConfigDict(extra="forbid")


class AnsatzConfig(BaseModel):
    type: Literal["real_amplitudes"] = "real_amplitudes"
    reps: int = Field(default=1, ge=1, le=4)
    entanglement: Literal["reverse_linear", "linear", "full", "circular"] = "reverse_linear"

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"type": "real_amplitudes", "reps": 1, "entanglement": "reverse_linear"}},
    )


class OptimizationVqeRequest(BaseModel):
    pauli_sum: list[PauliTerm] = Field(min_length=1)
    ansatz: AnsatzConfig = Field(default_factory=AnsatzConfig)
    optimizer: Phase5OptimizerConfig = Field(default_factory=Phase5OptimizerConfig)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "pauli_sum": [
                    {"pauli": "ZI", "coefficient": 1.0},
                    {"pauli": "IZ", "coefficient": -0.5},
                    {"pauli": "XX", "coefficient": 0.2},
                ],
                "ansatz": {"type": "real_amplitudes", "reps": 1},
                "optimizer": {"name": "cobyla", "maxiter": 25},
                "shots": 512,
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


class OptimizationVqeResponse(BaseModel):
    minimum_eigenvalue: float
    optimal_parameters: list[float]
    convergence: Phase5OptimizerMetadata
    provider: Phase5Provider = "qiskit-algorithms"
    backend_mode: str = "statevector_estimator"
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


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
    provider: Phase5Provider = "qiskit-experiments"
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
    provider: Phase5Provider = "qiskit-experiments"
    backend_mode: str = "aer_simulator"

    model_config = ConfigDict(extra="forbid")


class PortfolioBound(BaseModel):
    lower: int = Field(ge=0)
    upper: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_bounds(self) -> PortfolioBound:
        if self.upper < self.lower:
            raise ValueError("upper must be >= lower")
        return self


class FinancePortfolioOptimizationRequest(BaseModel):
    expected_returns: list[float] = Field(min_length=2, max_length=8)
    covariance_matrix: list[list[float]] = Field(min_length=2, max_length=8)
    budget: int = Field(ge=1)
    risk_factor: float = Field(gt=0.0, le=10.0)
    bounds: list[PortfolioBound] | None = None
    solver: Literal["qaoa", "exact"] = "qaoa"
    optimizer: Phase5OptimizerConfig = Field(default_factory=Phase5OptimizerConfig)
    reps: int = Field(default=1, ge=1, le=4)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "expected_returns": [0.1, 0.2, 0.12],
                "covariance_matrix": [
                    [0.05, 0.01, 0.02],
                    [0.01, 0.06, 0.01],
                    [0.02, 0.01, 0.04],
                ],
                "budget": 2,
                "risk_factor": 0.5,
                "solver": "qaoa",
                "optimizer": {"name": "cobyla", "maxiter": 25},
                "reps": 1,
                "shots": 512,
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
    def validate_shapes(self) -> FinancePortfolioOptimizationRequest:
        asset_count = len(self.expected_returns)
        if len(self.covariance_matrix) != asset_count:
            raise ValueError("covariance_matrix must have one row per expected return")
        for row in self.covariance_matrix:
            if len(row) != asset_count:
                raise ValueError("covariance_matrix must be square and match expected_returns length")
        if self.bounds is not None and len(self.bounds) != asset_count:
            raise ValueError("bounds length must match expected_returns length")
        if self.budget > asset_count:
            raise ValueError("budget cannot exceed the number of assets")
        return self


class FinanceConstraintSummary(BaseModel):
    budget: int
    selected_count: int

    model_config = ConfigDict(extra="forbid")


class FinancePortfolioOptimizationResponse(BaseModel):
    selected_allocation: list[int]
    objective_value: float
    constraint_summary: FinanceConstraintSummary
    solver_metadata: dict[str, Any]
    provider: Phase5Provider = "qiskit-finance"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")


class FeatureMapConfig(BaseModel):
    type: Literal["zz_feature_map"] = "zz_feature_map"
    reps: int = Field(default=1, ge=1, le=4)
    entanglement: Literal["linear", "full", "circular"] = "full"

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"}},
    )


class KernelClassifierRequest(BaseModel):
    training_features: list[list[float]] = Field(min_length=2, max_length=32)
    training_labels: list[int | str] = Field(min_length=2, max_length=32)
    prediction_features: list[list[float]] = Field(min_length=1, max_length=32)
    feature_map: FeatureMapConfig = Field(default_factory=FeatureMapConfig)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
                "training_labels": [0, 1, 1, 0],
                "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
                "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
                "seed": 7,
            }
        },
    )

    @model_validator(mode="after")
    def validate_shapes(self) -> KernelClassifierRequest:
        if len(self.training_features) != len(self.training_labels):
            raise ValueError("training_features and training_labels must have the same length")
        feature_dimension = len(self.training_features[0])
        if feature_dimension == 0:
            raise ValueError("feature vectors must not be empty")
        for row in [*self.training_features, *self.prediction_features]:
            if len(row) != feature_dimension:
                raise ValueError("all feature vectors must share the same dimension")
        return self


class KernelClassifierResponse(BaseModel):
    predictions: list[int | str]
    training_score: float
    support_vector_count: int
    training_metadata: dict[str, Any]
    provider: Phase5Provider = "qiskit-machine-learning"
    backend_mode: str = "fidelity_quantum_kernel"

    model_config = ConfigDict(extra="forbid")


class AtomCoordinate(BaseModel):
    symbol: str = Field(min_length=1)
    x: float
    y: float
    z: float

    model_config = ConfigDict(extra="forbid")


class NatureGroundStateEnergyRequest(BaseModel):
    atoms: list[AtomCoordinate] = Field(min_length=2, max_length=6)
    basis: str = Field(default="sto3g", min_length=1)
    charge: int = 0
    spin: int = 0
    mapper: Literal["jordan_wigner", "parity"] = "jordan_wigner"
    ansatz: AnsatzConfig = Field(default_factory=AnsatzConfig)
    optimizer: Phase5OptimizerConfig = Field(default_factory=Phase5OptimizerConfig)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "atoms": [
                    {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.0},
                    {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.735},
                ],
                "basis": "sto3g",
                "charge": 0,
                "spin": 0,
                "mapper": "jordan_wigner",
                "ansatz": {"type": "real_amplitudes", "reps": 1},
                "optimizer": {"name": "cobyla", "maxiter": 25},
                "seed": 7,
            }
        },
    )


class NatureMappedProblemSummary(BaseModel):
    mapper: str
    num_qubits: int
    num_spatial_orbitals: int
    num_particles: list[int]

    model_config = ConfigDict(extra="forbid")


class NatureGroundStateEnergyResponse(BaseModel):
    ground_state_energy: float
    total_energy: float | None = None
    nuclear_repulsion_energy: float | None = None
    mapped_problem_summary: NatureMappedProblemSummary
    solver_metadata: dict[str, Any]
    provider: Phase5Provider = "qiskit-nature"
    backend_mode: str = "statevector_estimator"

    model_config = ConfigDict(extra="forbid")
