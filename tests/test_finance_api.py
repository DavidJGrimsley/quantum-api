from __future__ import annotations

import pytest

from quantum_api.models.api import (
    FinancePortfolioDiversificationRequest,
    FinancePortfolioOptimizationRequest,
)
from quantum_api.services.finance.portfolio_diversification import solve_portfolio_diversification
from quantum_api.services.finance.portfolio_optimization import solve_portfolio_optimization
from quantum_api.services.quantum_runtime import runtime

requires_finance = pytest.mark.skipif(
    not (runtime.qiskit_finance_available and runtime.qiskit_optimization_available and runtime.qiskit_algorithms_available),
    reason="Finance dependencies unavailable",
)


def _finance_body(*, solver: str = "qaoa") -> dict[str, object]:
    return {
        "expected_returns": [0.1, 0.2, 0.12],
        "covariance_matrix": [
            [0.05, 0.01, 0.02],
            [0.01, 0.06, 0.01],
            [0.02, 0.01, 0.04],
        ],
        "budget": 2,
        "risk_factor": 0.5,
        "solver": solver,
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "reps": 1,
        "shots": 128,
        "seed": 7,
    }


def _diversification_body(*, solver: str = "exact") -> dict[str, object]:
    return {
        "similarity_matrix": [
            [1.0, 0.2, 0.3],
            [0.2, 1.0, 0.4],
            [0.3, 0.4, 1.0],
        ],
        "num_clusters": 2,
        "asset_labels": ["ALPHA", "BETA", "GAMMA"],
        "solver": solver,
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "reps": 1,
        "shots": 128,
        "seed": 7,
    }


@requires_finance
def test_finance_service_returns_allocation_for_exact_solver():
    payload = solve_portfolio_optimization(FinancePortfolioOptimizationRequest.model_validate(_finance_body(solver="exact")))
    assert sum(payload["selected_allocation"]) == 2
    assert payload["backend_mode"] == "numpy_minimum_eigensolver"


@requires_finance
def test_finance_diversification_service_returns_selected_assets():
    payload = solve_portfolio_diversification(
        FinancePortfolioDiversificationRequest.model_validate(_diversification_body())
    )
    assert len(payload["selected_asset_indices"]) == 2
    assert payload["selected_assets"] == ["ALPHA", "BETA"]
    assert payload["constraint_summary"]["num_clusters"] == 2


@requires_finance
def test_finance_endpoint_contract(client):
    response = client.post("/v1/finance/portfolio_optimization", json=_finance_body())
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "qiskit-finance"
    assert payload["constraint_summary"]["budget"] == 2

    diversification = client.post("/v1/finance/portfolio_diversification", json=_diversification_body())
    assert diversification.status_code == 200
    diversification_payload = diversification.json()
    assert diversification_payload["provider"] == "qiskit-finance"
    assert diversification_payload["constraint_summary"]["selected_count"] == 2


def test_finance_validation_rejects_non_square_covariance(client):
    payload = _finance_body()
    payload["covariance_matrix"] = [[0.05, 0.01], [0.01, 0.06], [0.02, 0.01]]
    response = client.post("/v1/finance/portfolio_optimization", json=payload)
    assert response.status_code == 422


def test_finance_diversification_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_finance_available", False)
    monkeypatch.setattr(runtime, "qiskit_finance_import_error", "missing for test")

    response = client.post("/v1/finance/portfolio_diversification", json=_diversification_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_finance_diversification_validation_rejects_non_symmetric_similarity_matrix(client):
    payload = _diversification_body()
    payload["similarity_matrix"][0][1] = 0.9
    response = client.post("/v1/finance/portfolio_diversification", json=payload)
    assert response.status_code == 422


@requires_finance
def test_finance_diversification_exact_results_are_stable():
    first = solve_portfolio_diversification(
        FinancePortfolioDiversificationRequest.model_validate(_diversification_body())
    )
    second = solve_portfolio_diversification(
        FinancePortfolioDiversificationRequest.model_validate(_diversification_body())
    )
    assert first["selected_asset_indices"] == second["selected_asset_indices"]
    assert first["objective_value"] == second["objective_value"]
