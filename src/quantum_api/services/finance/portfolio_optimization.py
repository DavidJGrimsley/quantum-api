from __future__ import annotations

import numpy as np

from quantum_api.models.finance import FinancePortfolioOptimizationRequest
from quantum_api.services.finance.common import solve_finance_quadratic_program


def solve_portfolio_optimization(request: FinancePortfolioOptimizationRequest) -> dict[str, object]:
    from qiskit_finance.applications import PortfolioOptimization

    bounds = None
    if request.bounds is not None:
        bounds = [(item.lower, item.upper) for item in request.bounds]

    application = PortfolioOptimization(
        expected_returns=np.asarray(request.expected_returns, dtype=float),
        covariances=np.asarray(request.covariance_matrix, dtype=float),
        risk_factor=float(request.risk_factor),
        budget=int(request.budget),
        bounds=bounds,
    )
    result, solver_metadata, backend_mode = solve_finance_quadratic_program(
        application.to_quadratic_program(),
        solver=request.solver,
        optimizer_config=request.optimizer,
        reps=request.reps,
        shots=request.shots,
        seed=request.seed,
    )

    selected_allocation = [int(round(float(item))) for item in result.x]
    return {
        "selected_allocation": selected_allocation,
        "objective_value": float(result.fval),
        "constraint_summary": {
            "budget": request.budget,
            "selected_count": sum(selected_allocation),
        },
        "solver_metadata": solver_metadata,
        "provider": "qiskit-finance",
        "backend_mode": backend_mode,
    }
