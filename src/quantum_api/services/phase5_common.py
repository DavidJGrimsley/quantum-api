from __future__ import annotations

from typing import Any

from quantum_api.models.phase5 import Phase5OptimizerConfig, Phase5OptimizerMetadata
from quantum_api.services.phase2_errors import Phase2ServiceError, ProviderUnavailableError


def ensure_dependency(
    *,
    available: bool,
    provider: str,
    import_error: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    if available:
        return

    payload = {"reason": "missing_dependency"}
    if import_error:
        payload["import_error"] = import_error
    if details:
        payload.update(details)
    raise ProviderUnavailableError(provider=provider, details=payload)


def build_optimizer(config: Phase5OptimizerConfig) -> Any:
    from qiskit_algorithms.optimizers import COBYLA, SLSQP, SPSA

    if config.name == "cobyla":
        return COBYLA(maxiter=config.maxiter, tol=config.tol)
    if config.name == "slsqp":
        return SLSQP(maxiter=config.maxiter, tol=config.tol)
    if config.name == "spsa":
        return SPSA(maxiter=config.maxiter)
    raise Phase2ServiceError(
        error="unsupported_optimizer",
        message=f"Unsupported optimizer '{config.name}'.",
        status_code=400,
        details={"optimizer": config.name},
    )


def optimizer_metadata_from_result(
    *,
    name: str,
    maxiter: int,
    result: Any,
) -> Phase5OptimizerMetadata:
    evaluations = getattr(result, "cost_function_evals", None)
    if evaluations is None:
        evaluations = getattr(result, "optimizer_evals", None)
    optimizer_time = getattr(result, "optimizer_time", None)
    return Phase5OptimizerMetadata(
        name=name,
        maxiter=maxiter,
        evaluations=int(evaluations) if evaluations is not None else None,
        optimizer_time_seconds=float(optimizer_time) if optimizer_time is not None else None,
    )


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
