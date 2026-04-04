from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from quantum_api.models.qiskit_common import AnsatzConfig, OptimizerConfig, QiskitDomainProvider


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
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
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
    provider: QiskitDomainProvider = "qiskit-nature"
    backend_mode: str = "statevector_estimator"

    model_config = ConfigDict(extra="forbid")
