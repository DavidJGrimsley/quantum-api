from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.qiskit_common import (
    AnsatzConfig,
    OptimizerConfig,
    OptimizerMetadata,
    PauliTerm,
    QiskitDomainProvider,
)


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
