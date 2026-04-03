from __future__ import annotations

import pytest

from quantum_api.models.api import RandomizedBenchmarkingRequest, StateTomographyRequest
from quantum_api.services.phase5_experiments import (
    run_randomized_benchmarking,
    run_state_tomography,
)
from quantum_api.services.quantum_runtime import runtime

requires_phase5_experiments = pytest.mark.skipif(
    not runtime.qiskit_experiments_available,
    reason="Phase 5 experiment dependencies unavailable",
)


def _tomography_body() -> dict[str, object]:
    return {
        "circuit": {
            "num_qubits": 1,
            "operations": [{"gate": "h", "target": 0}],
        },
        "shots": 128,
        "seed": 7,
        "target_statevector": [
            {"real": 0.70710678, "imag": 0.0},
            {"real": 0.70710678, "imag": 0.0},
        ],
    }


def _rb_body() -> dict[str, object]:
    return {
        "qubits": [0],
        "sequence_lengths": [1, 2, 4],
        "num_samples": 2,
        "shots": 128,
        "seed": 7,
    }


@requires_phase5_experiments
def test_state_tomography_service_returns_density_matrix():
    payload = run_state_tomography(StateTomographyRequest.model_validate(_tomography_body()))
    assert len(payload["reconstructed_density_matrix"]) == 2
    assert payload["state_fidelity"] is not None
    assert payload["positivity"]["positive"] is True


@requires_phase5_experiments
def test_randomized_benchmarking_service_returns_alpha_and_epc():
    payload = run_randomized_benchmarking(RandomizedBenchmarkingRequest.model_validate(_rb_body()))
    assert isinstance(payload["alpha"], float)
    assert "EPC" in payload["fit_metrics"]


@requires_phase5_experiments
def test_experiment_endpoints_contract(client):
    tomography = client.post("/v1/experiments/state_tomography", json=_tomography_body())
    assert tomography.status_code == 200
    assert tomography.json()["provider"] == "qiskit-experiments"

    benchmarking = client.post("/v1/experiments/randomized_benchmarking", json=_rb_body())
    assert benchmarking.status_code == 200
    assert "alpha" in benchmarking.json()


def test_state_tomography_validation_rejects_bad_target_length(client):
    payload = _tomography_body()
    payload["target_statevector"] = [{"real": 1.0, "imag": 0.0}]
    response = client.post("/v1/experiments/state_tomography", json=payload)
    assert response.status_code == 422


def test_experiment_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_experiments_available", False)
    monkeypatch.setattr(runtime, "qiskit_experiments_import_error", "missing for test")

    response = client.post("/v1/experiments/randomized_benchmarking", json=_rb_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"
