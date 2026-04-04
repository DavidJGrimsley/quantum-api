from __future__ import annotations

from quantum_api.models.experiments import StateTomographyRequest
from quantum_api.services.circuit_conversion import build_circuit_from_definition
from quantum_api.services.experiments.common import analysis_results_by_name, build_aer_backend
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.qiskit_common.serialization import complex_payload


def run_state_tomography(request: StateTomographyRequest) -> dict[str, object]:
    from qiskit.quantum_info import Statevector
    from qiskit_experiments.library import StateTomography

    circuit = build_circuit_from_definition(request.circuit)
    target = None
    if request.target_statevector is not None:
        target = Statevector(
            [complex(amplitude.real, amplitude.imag) for amplitude in request.target_statevector]
        )

    backend = build_aer_backend(seed=request.seed, purpose="state tomography")
    experiment = StateTomography(circuit, target=target if target is not None else "default")
    experiment_data = experiment.run(backend, shots=request.shots).block_for_results()
    analysis_results = analysis_results_by_name(experiment_data)
    state_result = analysis_results.get("state")
    if state_result is None:
        raise Phase2ServiceError(
            error="tomography_failed",
            message="State tomography did not produce a reconstructed state.",
            status_code=500,
        )

    density_matrix = getattr(state_result.value, "data", state_result.value)
    rows = [
        {"amplitudes": [complex_payload(item) for item in row]}
        for row in density_matrix
    ]
    extra = dict(getattr(state_result, "extra", {}) or {})
    positivity = {
        "positive": bool(extra.get("positive", False)),
        "rescaled_psd": bool(extra["rescaled_psd"]) if extra.get("rescaled_psd") is not None else None,
        "eigenvalues": [float(value) for value in extra.get("eigvals", [])],
        "raw_eigenvalues": [float(value) for value in extra.get("raw_eigvals", [])],
    }

    fidelity_result = analysis_results.get("state_fidelity")
    return {
        "reconstructed_density_matrix": rows,
        "trace": float(extra.get("trace", 0.0)),
        "positivity": positivity,
        "state_fidelity": float(fidelity_result.value) if fidelity_result is not None else None,
        "provider": "qiskit-experiments",
        "backend_mode": "aer_simulator",
    }
