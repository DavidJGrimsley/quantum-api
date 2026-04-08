from __future__ import annotations

import math

from quantum_api.models.experiments import T1ExperimentRequest
from quantum_api.services.experiments.common import analysis_results_by_name, build_aer_backend
from quantum_api.services.service_errors import QuantumApiServiceError
from quantum_api.services.qiskit_common.serialization import to_nominal_float


def run_t1_experiment(request: T1ExperimentRequest) -> dict[str, object]:
    from qiskit_experiments.library import T1

    backend = build_aer_backend(seed=request.seed, purpose="T1 characterization")
    experiment = T1(request.qubits, delays=request.delays)
    experiment_data = experiment.run(backend, shots=request.shots).block_for_results()
    analysis_results = analysis_results_by_name(experiment_data)
    t1_result = analysis_results.get("T1")
    if t1_result is None:
        raise QuantumApiServiceError(
            error="t1_failed",
            message="T1 analysis did not produce a fitted T1 value.",
            status_code=500,
        )

    t1_seconds = float(t1_result.value.nominal_value)
    if not math.isfinite(t1_seconds):
        raise QuantumApiServiceError(
            error="t1_failed",
            message="T1 analysis produced a non-finite fitted T1 value.",
            status_code=500,
        )

    # T1 is a decay constant and must be non-negative; clamp unstable fit artifacts.
    if t1_seconds < 0.0:
        t1_seconds = 0.0

    extra = dict(getattr(t1_result, "extra", {}) or {})
    return {
        "t1_seconds": t1_seconds,
        "fit_metrics": {
            "unit": extra.get("unit"),
            "run_time": to_nominal_float(extra.get("run_time")),
        },
        "provider": "qiskit-experiments",
        "backend_mode": "aer_simulator",
    }
