from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.qiskit_common import (
    AnsatzConfig,
    OptimizerConfig,
    OptimizerMetadata,
    PauliTerm,
    QiskitDomainProvider,
)

OptimizationApplicationSolver = Literal["qaoa", "exact"]


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
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
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
    optimizer_metadata: OptimizerMetadata
    provider: QiskitDomainProvider = "qiskit-algorithms"
    backend_mode: str = "statevector_sampler"
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class OptimizationVqeRequest(BaseModel):
    pauli_sum: list[PauliTerm] = Field(min_length=1)
    ansatz: AnsatzConfig = Field(default_factory=AnsatzConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
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
    convergence: OptimizerMetadata
    provider: QiskitDomainProvider = "qiskit-algorithms"
    backend_mode: str = "statevector_estimator"
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class WeightedGraphEdge(BaseModel):
    source: int = Field(ge=0)
    target: int = Field(ge=0)
    weight: float = 1.0

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_edge(self) -> WeightedGraphEdge:
        if self.source == self.target:
            raise ValueError("graph edges must connect two distinct nodes")
        if self.source > self.target:
            raise ValueError("graph edge indices must be ordered so source < target")
        return self


class OptimizationMaxcutRequest(BaseModel):
    num_nodes: int = Field(ge=2, le=10)
    edges: list[WeightedGraphEdge] = Field(min_length=1)
    solver: OptimizationApplicationSolver = "qaoa"
    reps: int = Field(default=1, ge=1, le=4)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "num_nodes": 3,
                "edges": [
                    {"source": 0, "target": 1, "weight": 1.5},
                    {"source": 1, "target": 2, "weight": 2.0},
                    {"source": 0, "target": 2, "weight": 0.5},
                ],
                "solver": "qaoa",
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

    @model_validator(mode="after")
    def validate_graph(self) -> OptimizationMaxcutRequest:
        seen_pairs: set[tuple[int, int]] = set()
        for edge in self.edges:
            if edge.source >= self.num_nodes or edge.target >= self.num_nodes:
                raise ValueError("graph edge indices must be within num_nodes")
            key = (edge.source, edge.target)
            if key in seen_pairs:
                raise ValueError("graph edges must be unique")
            seen_pairs.add(key)
        return self


class OptimizationMaxcutResponse(BaseModel):
    partition: list[list[int]]
    cut_value: float
    bitstring: str
    solver_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-optimization"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")


class OptimizationKnapsackRequest(BaseModel):
    item_values: list[int] = Field(min_length=1, max_length=12)
    item_weights: list[int] = Field(min_length=1, max_length=12)
    capacity: int = Field(ge=1)
    solver: OptimizationApplicationSolver = "qaoa"
    reps: int = Field(default=1, ge=1, le=4)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "item_values": [3, 4, 5],
                "item_weights": [2, 3, 4],
                "capacity": 5,
                "solver": "exact",
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

    @model_validator(mode="after")
    def validate_items(self) -> OptimizationKnapsackRequest:
        if len(self.item_values) != len(self.item_weights):
            raise ValueError("item_values and item_weights must have the same length")
        if any(value <= 0 for value in self.item_values):
            raise ValueError("item_values must all be positive integers")
        if any(weight <= 0 for weight in self.item_weights):
            raise ValueError("item_weights must all be positive integers")
        return self


class OptimizationKnapsackResponse(BaseModel):
    selected_items: list[int]
    total_value: int
    total_weight: int
    solver_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-optimization"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")


class OptimizationTspRequest(BaseModel):
    distance_matrix: list[list[float]] = Field(min_length=3, max_length=6)
    solver: OptimizationApplicationSolver = "qaoa"
    reps: int = Field(default=1, ge=1, le=4)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "distance_matrix": [
                    [0.0, 10.0, 15.0, 20.0],
                    [10.0, 0.0, 35.0, 25.0],
                    [15.0, 35.0, 0.0, 30.0],
                    [20.0, 25.0, 30.0, 0.0],
                ],
                "solver": "exact",
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

    @model_validator(mode="after")
    def validate_distance_matrix(self) -> OptimizationTspRequest:
        size = len(self.distance_matrix)
        for row in self.distance_matrix:
            if len(row) != size:
                raise ValueError("distance_matrix must be square")
        for i, row in enumerate(self.distance_matrix):
            for j, value in enumerate(row):
                if value < 0:
                    raise ValueError("distance_matrix values must be non-negative")
                if i == j and value != 0:
                    raise ValueError("distance_matrix diagonal entries must be zero")
                if self.distance_matrix[j][i] != value:
                    raise ValueError("distance_matrix must be symmetric")
        return self


class OptimizationTspResponse(BaseModel):
    tour_order: list[int]
    tour_length: float
    solver_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-optimization"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")
