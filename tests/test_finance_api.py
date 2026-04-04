from __future__ import annotations

import pytest

from quantum_api.models.api import FinancePortfolioOptimizationRequest
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


@requires_finance
def test_finance_service_returns_allocation_for_exact_solver():
    payload = solve_portfolio_optimization(FinancePortfolioOptimizationRequest.model_validate(_finance_body(solver="exact")))
    assert sum(payload["selected_allocation"]) == 2
    assert payload["backend_mode"] == "numpy_minimum_eigensolver"


@requires_finance
def test_finance_endpoint_contract(client):
    response = client.post("/v1/finance/portfolio_optimization", json=_finance_body())
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "qiskit-finance"
    assert payload["constraint_summary"]["budget"] == 2


def test_finance_validation_rejects_non_square_covariance(client):
    payload = _finance_body()
    payload["covariance_matrix"] = [[0.05, 0.01], [0.01, 0.06], [0.02, 0.01]]
    response = client.post("/v1/finance/portfolio_optimization", json=payload)
    assert response.status_code == 422
