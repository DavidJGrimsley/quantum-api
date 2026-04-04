from __future__ import annotations

import pytest

from quantum_api.models.api import (
    QuantumVolumeRequest,
    RandomizedBenchmarkingRequest,
    StateTomographyRequest,
    T1ExperimentRequest,
    T2RamseyExperimentRequest,
)
from quantum_api.services.experiments.quantum_volume import run_quantum_volume
from quantum_api.services.experiments.randomized_benchmarking import run_randomized_benchmarking
from quantum_api.services.experiments.state_tomography import run_state_tomography
from quantum_api.services.experiments.t1 import run_t1_experiment
from quantum_api.services.experiments.t2ramsey import run_t2ramsey_experiment
from quantum_api.services.quantum_runtime import runtime

requires_experiments = pytest.mark.skipif(
    not runtime.qiskit_experiments_available,
    reason="Experiment dependencies unavailable",
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


def _qv_body() -> dict[str, object]:
    return {
        "qubits": [0, 1],
        "trials": 3,
        "shots": 64,
        "seed": 7,
    }


def _t1_body() -> dict[str, object]:
    return {
        "qubits": [0],
        "delays": [0.000001, 0.000002, 0.000003, 0.000004],
        "shots": 64,
        "seed": 7,
    }


def _t2_body() -> dict[str, object]:
    return {
        "qubits": [0],
        "delays": [0.000001, 0.000002, 0.000003, 0.000004, 0.000005],
        "osc_freq": 100000.0,
        "shots": 64,
        "seed": 7,
    }


@requires_experiments
def test_state_tomography_service_returns_density_matrix():
    payload = run_state_tomography(StateTomographyRequest.model_validate(_tomography_body()))
    assert len(payload["reconstructed_density_matrix"]) == 2
    assert payload["state_fidelity"] is not None
    assert payload["positivity"]["positive"] is True


@requires_experiments
def test_randomized_benchmarking_service_returns_alpha_and_epc():
    payload = run_randomized_benchmarking(RandomizedBenchmarkingRequest.model_validate(_rb_body()))
    assert isinstance(payload["alpha"], float)
    assert "EPC" in payload["fit_metrics"]


@requires_experiments
def test_quantum_volume_service_returns_volume_summary():
    payload = run_quantum_volume(QuantumVolumeRequest.model_validate(_qv_body()))
    assert payload["quantum_volume"] >= 0
    assert "trials" in payload["analysis_metadata"]


@requires_experiments
def test_t1_service_returns_t1_seconds():
    payload = run_t1_experiment(T1ExperimentRequest.model_validate(_t1_body()))
    assert payload["t1_seconds"] >= 0.0
    assert payload["fit_metrics"]["unit"] == "s"


@requires_experiments
def test_t2ramsey_service_returns_t2star_seconds():
    payload = run_t2ramsey_experiment(T2RamseyExperimentRequest.model_validate(_t2_body()))
    assert payload["t2star_seconds"] >= 0.0
    assert payload["oscillation_frequency_hz"] is not None


@requires_experiments
def test_experiment_endpoints_contract(client):
    tomography = client.post("/v1/experiments/state_tomography", json=_tomography_body())
    assert tomography.status_code == 200
    assert tomography.json()["provider"] == "qiskit-experiments"

    benchmarking = client.post("/v1/experiments/randomized_benchmarking", json=_rb_body())
    assert benchmarking.status_code == 200
    assert "alpha" in benchmarking.json()

    quantum_volume = client.post("/v1/experiments/quantum_volume", json=_qv_body())
    assert quantum_volume.status_code == 200
    assert "quantum_volume" in quantum_volume.json()

    t1 = client.post("/v1/experiments/t1", json=_t1_body())
    assert t1.status_code == 200
    assert "t1_seconds" in t1.json()

    t2 = client.post("/v1/experiments/t2ramsey", json=_t2_body())
    assert t2.status_code == 200
    assert "t2star_seconds" in t2.json()


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


def test_t2ramsey_validation_rejects_unsorted_delays(client):
    payload = _t2_body()
    payload["delays"] = [0.000003, 0.000001, 0.000002, 0.000004, 0.000005]
    response = client.post("/v1/experiments/t2ramsey", json=payload)
    assert response.status_code == 422
