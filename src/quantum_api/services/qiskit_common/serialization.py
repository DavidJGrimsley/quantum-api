from __future__ import annotations

from collections.abc import Iterable
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


def amplitudes_payload(values: Any) -> list[dict[str, float]]:
    return [complex_payload(value) for value in values]


def float_pair_payload(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return [float(item) for item in value]
    return [float(value)]


def json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, complex):
        return complex_payload(value)
    if hasattr(value, "tolist"):
        return json_safe_value(value.tolist())
    if isinstance(value, dict):
        return {str(key): json_safe_value(item) for key, item in value.items()}
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [json_safe_value(item) for item in value]
    if hasattr(value, "nominal_value"):
        return float(value.nominal_value)
    if hasattr(value, "n"):
        return float(value.n)
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)
