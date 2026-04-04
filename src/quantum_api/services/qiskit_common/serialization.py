from __future__ import annotations

from typing import Any


def to_nominal_float(value: Any) -> float | None:
    if value is None:
        return None
    if hasattr(value, "nominal_value"):
        return float(value.nominal_value)
    if hasattr(value, "n"):
        return float(value.n)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def complex_payload(value: complex) -> dict[str, float]:
    complex_value = complex(value)
    return {
        "real": float(complex_value.real),
        "imag": float(complex_value.imag),
    }


def bitstring_from_vector(values: Any) -> str:
    return "".join(str(int(round(float(item)))) for item in values)
