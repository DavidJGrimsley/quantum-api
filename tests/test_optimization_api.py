from __future__ import annotations

import pytest

from quantum_api.models.api import (
    OptimizationKnapsackRequest,
    OptimizationMaxcutRequest,
    OptimizationQaoaRequest,
    OptimizationTspRequest,
    OptimizationVqeRequest,
)
from quantum_api.services.optimization.knapsack import solve_knapsack
from quantum_api.services.optimization.maxcut import solve_maxcut
from quantum_api.services.optimization.qaoa import solve_qaoa
from quantum_api.services.optimization.tsp import solve_tsp
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


def _maxcut_body(*, solver: str = "qaoa") -> dict[str, object]:
    return {
        "num_nodes": 3,
        "edges": [
            {"source": 0, "target": 1, "weight": 1.5},
            {"source": 1, "target": 2, "weight": 2.0},
            {"source": 0, "target": 2, "weight": 0.5},
        ],
        "solver": solver,
        "reps": 1,
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "shots": 128,
        "seed": 7,
    }


def _knapsack_body(*, solver: str = "exact") -> dict[str, object]:
    return {
        "item_values": [3, 4, 5],
        "item_weights": [2, 3, 4],
        "capacity": 5,
        "solver": solver,
        "reps": 1,
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "shots": 128,
        "seed": 7,
    }


def _tsp_body(*, solver: str = "exact") -> dict[str, object]:
    return {
        "distance_matrix": [
            [0.0, 10.0, 15.0, 20.0],
            [10.0, 0.0, 35.0, 25.0],
            [15.0, 35.0, 0.0, 30.0],
            [20.0, 25.0, 30.0, 0.0],
        ],
        "solver": solver,
        "reps": 1,
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
def test_maxcut_service_returns_partition_and_cut_value():
    payload = solve_maxcut(OptimizationMaxcutRequest.model_validate(_maxcut_body(solver="exact")))
    assert sorted(node for group in payload["partition"] for node in group) == [0, 1, 2]
    assert payload["cut_value"] == pytest.approx(3.5)
    assert payload["solver_metadata"]["solver"] == "exact"


@requires_optimization
def test_knapsack_service_returns_selected_items_and_totals():
    payload = solve_knapsack(OptimizationKnapsackRequest.model_validate(_knapsack_body()))
    assert payload["selected_items"] == [0, 1]
    assert payload["total_value"] == 7
    assert payload["total_weight"] == 5


@requires_optimization
def test_tsp_service_returns_tour_summary():
    payload = solve_tsp(OptimizationTspRequest.model_validate(_tsp_body()))
    assert set(payload["tour_order"]) == {0, 1, 2, 3}
    assert len(payload["tour_order"]) == 4
    assert payload["tour_length"] == pytest.approx(80.0)


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

    maxcut = client.post("/v1/optimization/maxcut", json=_maxcut_body())
    assert maxcut.status_code == 200
    assert maxcut.json()["provider"] == "qiskit-optimization"
    assert maxcut.json()["bitstring"]

    knapsack = client.post("/v1/optimization/knapsack", json=_knapsack_body())
    assert knapsack.status_code == 200
    assert knapsack.json()["selected_items"] == [0, 1]

    tsp = client.post("/v1/optimization/tsp", json=_tsp_body())
    assert tsp.status_code == 200
    assert tsp.json()["tour_length"] == pytest.approx(80.0)


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


def test_maxcut_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_optimization_available", False)
    monkeypatch.setattr(runtime, "qiskit_optimization_import_error", "missing for test")

    response = client.post("/v1/optimization/maxcut", json=_maxcut_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_tsp_validation_rejects_non_symmetric_distance_matrix(client):
    payload = _tsp_body()
    payload["distance_matrix"][0][1] = 9.0
    response = client.post("/v1/optimization/tsp", json=payload)
    assert response.status_code == 422


@requires_optimization
def test_maxcut_qaoa_seeded_results_are_stable():
    first = solve_maxcut(OptimizationMaxcutRequest.model_validate(_maxcut_body()))
    second = solve_maxcut(OptimizationMaxcutRequest.model_validate(_maxcut_body()))
    assert first["bitstring"] == second["bitstring"]
    assert first["cut_value"] == second["cut_value"]
