from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

QiskitDomainProvider = Literal[
    "qiskit-algorithms",
    "qiskit-experiments",
    "qiskit-finance",
    "qiskit-machine-learning",
    "qiskit-nature",
]


class OptimizerConfig(BaseModel):
    name: Literal["cobyla", "slsqp", "spsa"] = "cobyla"
    maxiter: int = Field(default=100, ge=1, le=500)
    tol: float | None = Field(default=None, gt=0.0)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "cobyla", "maxiter": 50, "tol": 0.001}},
    )


class OptimizerMetadata(BaseModel):
    name: str
    maxiter: int
    evaluations: int | None = None
    optimizer_time_seconds: float | None = None

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
