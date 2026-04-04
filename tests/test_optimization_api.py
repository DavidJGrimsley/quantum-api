from __future__ import annotations

import pytest

from quantum_api.models.api import OptimizationQaoaRequest, OptimizationVqeRequest
from quantum_api.services.optimization.qaoa import solve_qaoa
from quantum_api.services.optimization.vqe import solve_vqe
from quantum_api.services.quantum_runtime import runtime

requires_optimization = pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Optimization dependencies unavailable",
)


def _qaoa_body() -> dict[str, object]:
    return {
        "problem": {
            "num_variables": 2,
            "linear": [1.0, -2.0],
            "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
            "sense": "minimize",
        },
        "reps": 1,
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "shots": 128,
        "seed": 7,
    }


def _vqe_body() -> dict[str, object]:
    return {
        "pauli_sum": [
            {"pauli": "ZI", "coefficient": 1.0},
            {"pauli": "IZ", "coefficient": -0.5},
            {"pauli": "XX", "coefficient": 0.2},
        ],
        "ansatz": {"type": "real_amplitudes", "reps": 1},
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "shots": 128,
        "seed": 7,
    }


@requires_optimization
def test_qaoa_service_returns_best_solution_and_samples():
    payload = solve_qaoa(OptimizationQaoaRequest.model_validate(_qaoa_body()))
    assert payload["best_bitstring"] in {"01", "10", "00", "11"}
    assert payload["solution_samples"]
    assert payload["optimizer_metadata"]["name"] == "cobyla"


@requires_optimization
def test_vqe_service_returns_eigenvalue_and_parameters():
    payload = solve_vqe(OptimizationVqeRequest.model_validate(_vqe_body()))
    assert isinstance(payload["minimum_eigenvalue"], float)
    assert payload["optimal_parameters"]
    assert payload["convergence"]["name"] == "cobyla"


@requires_optimization
def test_optimization_endpoints_contract(client):
    qaoa = client.post("/v1/optimization/qaoa", json=_qaoa_body())
    assert qaoa.status_code == 200
    assert "best_bitstring" in qaoa.json()
    assert qaoa.json()["provider"] == "qiskit-algorithms"

    vqe = client.post("/v1/optimization/vqe", json=_vqe_body())
    assert vqe.status_code == 200
    assert "minimum_eigenvalue" in vqe.json()
    assert vqe.json()["backend_mode"] == "statevector_estimator"


def test_optimization_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_algorithms_available", False)
    monkeypatch.setattr(runtime, "qiskit_algorithms_import_error", "missing for test")

    response = client.post("/v1/optimization/qaoa", json=_qaoa_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_vqe_invalid_pauli_term_returns_400(client):
    payload = _vqe_body()
    payload["pauli_sum"] = [{"pauli": "AZ", "coefficient": 1.0}]
    response = client.post("/v1/optimization/vqe", json=payload)
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pauli_term"
