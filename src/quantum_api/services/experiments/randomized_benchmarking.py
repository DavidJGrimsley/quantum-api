from __future__ import annotations

from quantum_api.models.experiments import RandomizedBenchmarkingRequest
from quantum_api.services.experiments.common import build_aer_backend
from quantum_api.services.qiskit_common.serialization import to_nominal_float
from quantum_api.services.service_errors import QuantumApiServiceError


def run_randomized_benchmarking(request: RandomizedBenchmarkingRequest) -> dict[str, object]:
    from qiskit_experiments.library import StandardRB

    backend = build_aer_backend(seed=request.seed, purpose="randomized benchmarking")
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
        raise QuantumApiServiceError(
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
