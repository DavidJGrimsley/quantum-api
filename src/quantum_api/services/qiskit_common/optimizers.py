from __future__ import annotations

from typing import Any

from quantum_api.models.qiskit_common import OptimizerConfig, OptimizerMetadata
from quantum_api.services.phase2_errors import Phase2ServiceError


def build_optimizer(config: OptimizerConfig) -> Any:
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
) -> OptimizerMetadata:
    evaluations = getattr(result, "cost_function_evals", None)
    if evaluations is None:
        evaluations = getattr(result, "optimizer_evals", None)
    optimizer_time = getattr(result, "optimizer_time", None)
    return OptimizerMetadata(
        name=name,
        maxiter=maxiter,
        evaluations=int(evaluations) if evaluations is not None else None,
        optimizer_time_seconds=float(optimizer_time) if optimizer_time is not None else None,
    )
