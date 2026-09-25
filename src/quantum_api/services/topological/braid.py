from __future__ import annotations

import cmath
import math
import random
from collections.abc import Sequence

from quantum_api.models.topological import BraidOperation, TopologicalBraidRequest

Matrix2 = tuple[tuple[complex, complex], tuple[complex, complex]]
Vector2 = tuple[complex, complex]

_CONVENTION = "fibonacci_nayak_rmp_2008_chiral"
_PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Fusion-basis change for three Fibonacci anyons with total charge tau.
_F: Matrix2 = (
    (1.0 / _PHI, 1.0 / math.sqrt(_PHI)),
    (1.0 / math.sqrt(_PHI), -1.0 / _PHI),
)

# Exchange phases for tau x tau -> 1 and tau x tau -> tau.
_R: Matrix2 = (
    (cmath.exp(-4j * math.pi / 5.0), 0j),
    (0j, -cmath.exp(-2j * math.pi / 5.0)),
)


def _matmul(left: Matrix2, right: Matrix2) -> Matrix2:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _matvec(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def _dagger(matrix: Matrix2) -> Matrix2:
    return (
        (matrix[0][0].conjugate(), matrix[1][0].conjugate()),
        (matrix[0][1].conjugate(), matrix[1][1].conjugate()),
    )


_SIGMA_1: Matrix2 = _R
_SIGMA_2: Matrix2 = _matmul(_matmul(_dagger(_F), _R), _F)


def braid_generator(generator: int, power: int = 1) -> Matrix2:
    """Return sigma_1 or sigma_2 (or its inverse) for the fixed v1 model."""

    if generator == 1:
        matrix = _SIGMA_1
    elif generator == 2:
        matrix = _SIGMA_2
    else:
        raise ValueError("generator must be 1 or 2")

    if power == 1:
        return matrix
    if power == -1:
        return _dagger(matrix)
    raise ValueError("power must be -1 or 1")


def evaluate_state(
    initial_state: str,
    braid_word: Sequence[BraidOperation],
) -> Vector2:
    state: Vector2 = (1 + 0j, 0j) if initial_state == "0" else (0j, 1 + 0j)

    for operation in braid_word:
        state = _matvec(braid_generator(operation.generator, operation.power), state)

    # Remove tiny floating-point norm drift while preserving phase.
    norm = math.sqrt(abs(state[0]) ** 2 + abs(state[1]) ** 2)
    if norm == 0:
        raise ValueError("braid evaluation produced a zero-norm state")
    return (state[0] / norm, state[1] / norm)


def _sample_channel(vacuum_probability: float, rng: random.Random) -> str:
    return "vacuum" if rng.random() < vacuum_probability else "tau"


def run_topological_braid(request: TopologicalBraidRequest) -> dict[str, object]:
    """Evaluate a Fibonacci braid and optionally sample fusion measurements."""

    state = evaluate_state(request.initial_state, request.braid_word)
    vacuum_probability = float(abs(state[0]) ** 2)
    tau_probability = float(abs(state[1]) ** 2)

    # Clamp tiny floating point artifacts and normalize once more for stable JSON.
    vacuum_probability = min(1.0, max(0.0, vacuum_probability))
    tau_probability = min(1.0, max(0.0, tau_probability))
    total = vacuum_probability + tau_probability
    if total:
        vacuum_probability /= total
        tau_probability /= total

    measurement: str | None = None
    counts: dict[str, int] | None = None
    effective_shots = 0

    if request.measure:
        effective_shots = request.shots if request.shots > 0 else 1
        rng = random.Random(request.seed)
        samples = [_sample_channel(vacuum_probability, rng) for _ in range(effective_shots)]
        measurement = samples[0]
        counts = {
            "vacuum": samples.count("vacuum"),
            "tau": samples.count("tau"),
        }

    return {
        "model": "fibonacci",
        "anyon_count": 3,
        "total_charge": "tau",
        "initial_state": request.initial_state,
        "braid_word": [operation.model_dump() for operation in request.braid_word],
        "logical_state": [
            {"real": float(state[0].real), "imag": float(state[0].imag)},
            {"real": float(state[1].real), "imag": float(state[1].imag)},
        ],
        "fusion_probabilities": {
            "vacuum": vacuum_probability,
            "tau": tau_probability,
        },
        "measurement": measurement,
        "shots": effective_shots,
        "counts": counts,
        "metadata": {
            "simulation_type": "digital_simulation_of_fibonacci_braid",
            "convention": _CONVENTION,
            "logical_dimension": 2,
        },
    }
