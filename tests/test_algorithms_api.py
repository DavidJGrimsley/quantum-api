from __future__ import annotations

import pytest

from quantum_api.models.api import (
    AmplitudeEstimationRequest,
    GroverSearchRequest,
    PhaseEstimationRequest,
    TimeEvolutionRequest,
)
from quantum_api.services.algorithms.amplitude_estimation import run_amplitude_estimation
from quantum_api.services.algorithms.grover_search import run_grover_search
from quantum_api.services.algorithms.phase_estimation import run_phase_estimation
from quantum_api.services.algorithms.time_evolution import run_time_evolution
from quantum_api.services.quantum_runtime import runtime

requires_algorithms = pytest.mark.skipif(
    not runtime.qiskit_algorithms_available,
    reason="Algorithm dependencies unavailable",
)


def _grover_body() -> dict[str, object]:
    return {
        "marked_bitstrings": ["11"],
        "iterations": [1],
        "shots": 128,
        "seed": 7,
    }


def _amplitude_body() -> dict[str, object]:
    return {
        "variant": "ae",
        "state_preparation": {
            "num_qubits": 1,
            "operations": [{"gate": "ry", "target": 0, "theta": 1.2}],
        },
        "objective_qubits": [0],
        "num_eval_qubits": 2,
        "shots": 128,
        "seed": 7,
    }


def _phase_body() -> dict[str, object]:
    return {
        "variant": "standard",
        "unitary": {
            "num_qubits": 1,
            "operations": [{"gate": "z", "target": 0}],
        },
        "state_preparation": {
            "num_qubits": 1,
            "operations": [{"gate": "h", "target": 0}],
        },
        "num_evaluation_qubits": 3,
        "shots": 128,
        "seed": 7,
    }


def _time_body() -> dict[str, object]:
    return {
        "variant": "trotter_qrte",
        "hamiltonian": [{"pauli": "Z", "coefficient": 1.0}],
        "time": 0.5,
        "initial_state": {
            "num_qubits": 1,
            "operations": [{"gate": "h", "target": 0}],
        },
        "num_timesteps": 2,
        "shots": 128,
        "seed": 7,
    }


@requires_algorithms
def test_grover_service_returns_top_measurement_and_counts():
    payload = run_grover_search(GroverSearchRequest.model_validate(_grover_body()))
    assert payload["top_measurement"] == "11"
    assert payload["counts"]["11"] == 128
    assert payload["good_state_found"] is True


@requires_algorithms
def test_amplitude_estimation_service_returns_estimate_and_metadata():
    payload = run_amplitude_estimation(AmplitudeEstimationRequest.model_validate(_amplitude_body()))
    assert isinstance(payload["estimate"], float)
    assert payload["raw_metadata"]["num_oracle_queries"] >= 0


@requires_algorithms
def test_phase_estimation_service_returns_phase_distribution():
    payload = run_phase_estimation(PhaseEstimationRequest.model_validate(_phase_body()))
    assert payload["most_likely_phase"] >= 0.0
    assert payload["phase_distribution"]


@requires_algorithms
def test_time_evolution_service_returns_final_state_payload():
    payload = run_time_evolution(TimeEvolutionRequest.model_validate(_time_body()))
    assert payload["final_state_operations"]
    assert payload["final_statevector"]
    assert payload["variant"] == "trotter_qrte"


@requires_algorithms
def test_algorithm_endpoints_contract(client):
    grover = client.post("/v1/algorithms/grover_search", json=_grover_body())
    assert grover.status_code == 200
    assert grover.json()["provider"] == "qiskit-algorithms"

    amplitude = client.post("/v1/algorithms/amplitude_estimation", json=_amplitude_body())
    assert amplitude.status_code == 200
    assert "estimate" in amplitude.json()

    phase = client.post("/v1/algorithms/phase_estimation", json=_phase_body())
    assert phase.status_code == 200
    assert "most_likely_phase" in phase.json()

    time_evolution = client.post("/v1/algorithms/time_evolution", json=_time_body())
    assert time_evolution.status_code == 200
    assert "final_state_operations" in time_evolution.json()


@requires_algorithms
def test_seeded_algorithm_results_are_stable():
    grover_first = run_grover_search(GroverSearchRequest.model_validate(_grover_body()))
    grover_second = run_grover_search(GroverSearchRequest.model_validate(_grover_body()))
    assert grover_first["counts"] == grover_second["counts"]

    amplitude_first = run_amplitude_estimation(AmplitudeEstimationRequest.model_validate(_amplitude_body()))
    amplitude_second = run_amplitude_estimation(AmplitudeEstimationRequest.model_validate(_amplitude_body()))
    assert amplitude_first["estimate"] == amplitude_second["estimate"]

    phase_first = run_phase_estimation(PhaseEstimationRequest.model_validate(_phase_body()))
    phase_second = run_phase_estimation(PhaseEstimationRequest.model_validate(_phase_body()))
    assert phase_first["most_likely_phase"] == phase_second["most_likely_phase"]


def test_algorithm_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_algorithms_available", False)
    monkeypatch.setattr(runtime, "qiskit_algorithms_import_error", "missing for test")

    response = client.post("/v1/algorithms/grover_search", json=_grover_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_amplitude_estimation_validation_rejects_missing_variant_fields(client):
    payload = _amplitude_body()
    payload.pop("num_eval_qubits")
    response = client.post("/v1/algorithms/amplitude_estimation", json=payload)
    assert response.status_code == 422


def test_phase_estimation_hamiltonian_variant_rejects_empty_hamiltonian(client):
    response = client.post(
        "/v1/algorithms/phase_estimation",
        json={
            "variant": "hamiltonian",
            "hamiltonian": [],
            "num_evaluation_qubits": 3,
            "shots": 128,
            "seed": 7,
        },
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_hamiltonian"


def test_time_evolution_validation_rejects_missing_initial_state_for_trotter(client):
    payload = _time_body()
    payload.pop("initial_state")
    response = client.post("/v1/algorithms/time_evolution", json=payload)
    assert response.status_code == 422
