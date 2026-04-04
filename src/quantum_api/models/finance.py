from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum_api.config import get_settings
from quantum_api.models.qiskit_common import OptimizerConfig, QiskitDomainProvider

FinanceSolver = Literal["qaoa", "exact"]


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
    solver: FinanceSolver = "qaoa"
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
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
    provider: QiskitDomainProvider = "qiskit-finance"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")


class FinancePortfolioDiversificationRequest(BaseModel):
    similarity_matrix: list[list[float]] = Field(min_length=2, max_length=4)
    num_clusters: int = Field(ge=1)
    asset_labels: list[str] | None = None
    solver: FinanceSolver = "qaoa"
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    reps: int = Field(default=1, ge=1, le=4)
    shots: int = Field(default=1024, ge=1)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "similarity_matrix": [
                    [1.0, 0.2, 0.3],
                    [0.2, 1.0, 0.4],
                    [0.3, 0.4, 1.0],
                ],
                "num_clusters": 2,
                "asset_labels": ["ALPHA", "BETA", "GAMMA"],
                "solver": "exact",
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
    def validate_shapes(self) -> FinancePortfolioDiversificationRequest:
        asset_count = len(self.similarity_matrix)
        for row in self.similarity_matrix:
            if len(row) != asset_count:
                raise ValueError("similarity_matrix must be square")
        for i, row in enumerate(self.similarity_matrix):
            for j, value in enumerate(row):
                if value < 0:
                    raise ValueError("similarity_matrix values must be non-negative")
                if self.similarity_matrix[j][i] != value:
                    raise ValueError("similarity_matrix must be symmetric")
                if i == j and value <= 0:
                    raise ValueError("similarity_matrix diagonal values must be positive")
        if self.asset_labels is not None and len(self.asset_labels) != asset_count:
            raise ValueError("asset_labels length must match similarity_matrix size")
        if self.num_clusters > asset_count:
            raise ValueError("num_clusters cannot exceed the number of assets")
        return self


class FinanceDiversificationConstraintSummary(BaseModel):
    num_assets: int
    num_clusters: int
    selected_count: int

    model_config = ConfigDict(extra="forbid")


class FinancePortfolioDiversificationResponse(BaseModel):
    selected_asset_indices: list[int]
    selected_assets: list[str] | None = None
    objective_value: float
    constraint_summary: FinanceDiversificationConstraintSummary
    solver_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-finance"
    backend_mode: str

    model_config = ConfigDict(extra="forbid")
