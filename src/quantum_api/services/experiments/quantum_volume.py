from __future__ import annotations

from quantum_api.models.experiments import QuantumVolumeRequest
from quantum_api.services.experiments.common import analysis_results_by_name, build_aer_backend
from quantum_api.services.qiskit_common.serialization import to_nominal_float
from quantum_api.services.service_errors import QuantumApiServiceError


def run_quantum_volume(request: QuantumVolumeRequest) -> dict[str, object]:
    from qiskit_experiments.library import QuantumVolume

    backend = build_aer_backend(seed=request.seed, purpose="quantum volume")
    experiment = QuantumVolume(
        request.qubits,
        trials=request.trials,
        seed=request.seed,
    )
    experiment_data = experiment.run(backend, shots=request.shots).block_for_results()
    analysis_results = analysis_results_by_name(experiment_data)
    mean_hop_result = analysis_results.get("mean_HOP")
    qv_result = analysis_results.get("quantum_volume")
    if qv_result is None:
        raise QuantumApiServiceError(
            error="quantum_volume_failed",
            message="Quantum volume analysis did not produce a volume result.",
            status_code=500,
        )

    extra = dict(getattr(qv_result, "extra", {}) or {})
    return {
        "quantum_volume": int(qv_result.value),
        "mean_heavy_output_probability": (
            to_nominal_float(mean_hop_result.value) if mean_hop_result is not None else None
        ),
        "analysis_metadata": {
            "success": extra.get("success"),
            "confidence": to_nominal_float(extra.get("confidence")),
            "depth": int(extra["depth"]) if extra.get("depth") is not None else None,
            "trials": int(extra["trials"]) if extra.get("trials") is not None else None,
        },
        "provider": "qiskit-experiments",
        "backend_mode": "aer_simulator",
    }
