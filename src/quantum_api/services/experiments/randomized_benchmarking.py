from __future__ import annotations

from quantum_api.models.experiments import RandomizedBenchmarkingRequest
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.serialization import to_nominal_float
from quantum_api.services.quantum_runtime import runtime


def run_randomized_benchmarking(request: RandomizedBenchmarkingRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_experiments_available,
        provider="qiskit-experiments",
        import_error=runtime.qiskit_experiments_import_error,
    )
    if runtime.AerSimulator is None:
        raise Phase2ServiceError(
            error="provider_unavailable",
            message="Aer simulator is unavailable for randomized benchmarking.",
            status_code=503,
            details={"reason": "missing_aer_simulator"},
        )

    from qiskit_experiments.library import StandardRB

    backend = runtime.AerSimulator(seed_simulator=request.seed) if request.seed is not None else runtime.AerSimulator()
    experiment = StandardRB(
        tuple(request.qubits),
        lengths=request.sequence_lengths,
        num_samples=request.num_samples,
        seed=request.seed,
    )
    experiment_data = experiment.run(backend, shots=request.shots).block_for_results()
    metrics = {
        result.name: to_nominal_float(result.value)
        for result in experiment_data.analysis_results()
    }
    alpha = metrics.get("alpha")
    epc = metrics.get("EPC")
    if alpha is None or epc is None:
        raise Phase2ServiceError(
            error="benchmarking_failed",
            message="Randomized benchmarking did not produce alpha/EPC metrics.",
            status_code=500,
        )
    return {
        "alpha": alpha,
        "epc": epc,
        "fit_metrics": metrics,
        "provider": "qiskit-experiments",
        "backend_mode": "aer_simulator",
    }
