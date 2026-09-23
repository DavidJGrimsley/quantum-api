"""Bounded integers assembled from ordered, single-qubit measurements."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from quantum_api.models.core import RandomIntResponse
from quantum_api.services.quantum_core import Qubit
from quantum_api.services.quantum_runtime import runtime


def random_bit_width(minimum: int, maximum: int) -> int:
    return (maximum - minimum).bit_length()


def random_job_shots(minimum: int, maximum: int) -> int:
    span = maximum - minimum + 1
    candidates = 1 if span & (span - 1) == 0 else 32
    return max(1, random_bit_width(minimum, maximum) * candidates)


class RandomResultError(ValueError):
    """A stable, credential-safe error for persisted random job failures."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def bounded_value(bits: Iterable[int], minimum: int, maximum: int) -> int:
    """Consume candidates in measurement order; discard out-of-range candidates."""
    if minimum == maximum:
        return minimum
    width = random_bit_width(minimum, maximum)
    span = maximum - minimum + 1
    iterator = iter(bits)
    while True:
        candidate = 0
        for _ in range(width):
            try:
                bit = next(iterator)
            except StopIteration as exc:
                raise RandomResultError(
                    "rejection_exhausted", "No in-range candidate in the submitted measurements."
                ) from exc
            candidate = (candidate << 1) | bit
        if candidate < span:
            return minimum + candidate


def generate_random(minimum: int, maximum: int) -> RandomIntResponse:
    qubit = Qubit()

    def measurements() -> Iterable[int]:
        while True:
            qubit.hadamard()
            yield qubit.measure()

    return RandomIntResponse(
        value=bounded_value(measurements(), minimum, maximum),
        source="qiskit-simulator" if runtime.qiskit_available else "classical-fallback",
    )


def random_value_from_result(raw_result: Any, minimum: int, maximum: int) -> int:
    """Only ordered BitArray shots are sufficient; counts lose measurement order."""
    try:
        if len(raw_result) != 1:
            raise ValueError("Expected one PUB result")
        register = raw_result[0].data.meas
        bitstrings = register.get_bitstrings()
        if (
            not isinstance(bitstrings, list)
            or len(bitstrings) != random_job_shots(minimum, maximum)
            or any(not isinstance(bit, str) or bit not in {"0", "1"} for bit in bitstrings)
        ):
            raise ValueError("Expected the submitted number of one-bit measurements")
    except Exception as exc:
        raise RandomResultError(
            "malformed_provider_result", "IBM returned invalid ordered single-qubit measurements."
        ) from exc
    return bounded_value((int(bit) for bit in bitstrings), minimum, maximum)
