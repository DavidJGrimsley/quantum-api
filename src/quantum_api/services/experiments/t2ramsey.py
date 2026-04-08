from __future__ import annotations

from quantum_api.models.experiments import T2RamseyExperimentRequest
from quantum_api.services.experiments.common import analysis_results_by_name, build_aer_backend
from quantum_api.services.service_errors import QuantumApiServiceError
from quantum_api.services.qiskit_common.serialization import to_nominal_float


def run_t2ramsey_experiment(request: T2RamseyExperimentRequest) -> dict[str, object]:
    from qiskit_experiments.library import T2Ramsey

    backend = build_aer_backend(seed=request.seed, purpose="T2 Ramsey characterization")
    experiment = T2Ramsey(request.qubits, delays=request.delays, osc_freq=request.osc_freq)
    experiment_data = experiment.run(backend, shots=request.shots).block_for_results()
    analysis_results = analysis_results_by_name(experiment_data)
    t2_result = analysis_results.get("T2star")
    freq_result = analysis_results.get("Frequency")
    if t2_result is None:
        raise QuantumApiServiceError(
            error="t2ramsey_failed",
            message="T2 Ramsey analysis did not produce a fitted T2* value.",
            status_code=500,
        )

    extra = dict(getattr(t2_result, "extra", {}) or {})
    return {
        "t2star_seconds": float(t2_result.value.nominal_value),
        "oscillation_frequency_hz": (
            float(freq_result.value.nominal_value)
            if freq_result is not None
            else None
        ),
        "fit_metrics": {
            "unit": extra.get("unit"),
            "run_time": to_nominal_float(extra.get("run_time")),
        },
        "provider": "qiskit-experiments",
        "backend_mode": "aer_simulator",
    }
