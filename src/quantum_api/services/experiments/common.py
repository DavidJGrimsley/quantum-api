from __future__ import annotations

from typing import Any

from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def build_aer_backend(*, seed: int | None, purpose: str) -> Any:
    ensure_dependency(
        available=runtime.qiskit_experiments_available,
        provider="qiskit-experiments",
        import_error=runtime.qiskit_experiments_import_error,
    )
    if runtime.AerSimulator is None:
        raise Phase2ServiceError(
            error="provider_unavailable",
            message=f"Aer simulator is unavailable for {purpose}.",
            status_code=503,
            details={"reason": "missing_aer_simulator"},
        )
    return runtime.AerSimulator(seed_simulator=seed) if seed is not None else runtime.AerSimulator()


def analysis_results_by_name(experiment_data: Any) -> dict[str, Any]:
    return {
        result.name: result
        for result in experiment_data.analysis_results()
    }
