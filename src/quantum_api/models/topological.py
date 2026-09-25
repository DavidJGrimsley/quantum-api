from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BraidOperation(BaseModel):
    """One generator in a three-strand braid word."""

    generator: Literal[1, 2]
    power: Literal[-1, 1] = 1

    model_config = ConfigDict(extra="forbid")


class TopologicalBraidRequest(BaseModel):
    """Evaluate a small Fibonacci-anyon braid.

    v1 intentionally fixes the model to three Fibonacci anyons with total
    charge tau. This keeps the public contract useful for games and demos
    without pretending to be a general anyon simulator.
    """

    model: Literal["fibonacci"] = "fibonacci"
    anyon_count: Literal[3] = 3
    total_charge: Literal["tau"] = "tau"
    initial_state: Literal["0", "1"] = "0"
    braid_word: list[BraidOperation] = Field(default_factory=list, max_length=256)
    measure: bool = False
    shots: int = Field(default=0, ge=0, le=4096)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "model": "fibonacci",
                "anyon_count": 3,
                "total_charge": "tau",
                "initial_state": "0",
                "braid_word": [
                    {"generator": 1, "power": 1},
                    {"generator": 2, "power": 1},
                    {"generator": 1, "power": -1},
                ],
                "measure": True,
                "shots": 1,
                "seed": 7,
            }
        },
    )


class ComplexValue(BaseModel):
    real: float
    imag: float

    model_config = ConfigDict(extra="forbid")


class FusionProbabilities(BaseModel):
    vacuum: float
    tau: float

    model_config = ConfigDict(extra="forbid")


class TopologicalBraidMetadata(BaseModel):
    simulation_type: Literal["digital_simulation_of_fibonacci_braid"]
    convention: str
    logical_dimension: Literal[2] = 2

    model_config = ConfigDict(extra="forbid")


class TopologicalBraidResponse(BaseModel):
    model: Literal["fibonacci"]
    anyon_count: Literal[3]
    total_charge: Literal["tau"]
    initial_state: Literal["0", "1"]
    braid_word: list[BraidOperation]
    logical_state: list[ComplexValue]
    fusion_probabilities: FusionProbabilities
    measurement: Literal["vacuum", "tau"] | None = None
    shots: int = 0
    counts: dict[str, int] | None = None
    metadata: TopologicalBraidMetadata

    model_config = ConfigDict(extra="forbid")
