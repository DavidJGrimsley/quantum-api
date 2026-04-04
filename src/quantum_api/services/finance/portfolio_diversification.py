from __future__ import annotations

import numpy as np

from quantum_api.models.finance import FinancePortfolioDiversificationRequest
from quantum_api.services.finance.common import solve_finance_quadratic_program


def solve_portfolio_diversification(request: FinancePortfolioDiversificationRequest) -> dict[str, object]:
    from qiskit_finance.applications import PortfolioDiversification

    similarity_matrix = np.asarray(request.similarity_matrix, dtype=float)
    num_assets = len(request.similarity_matrix)
    application = PortfolioDiversification(
        similarity_matrix=similarity_matrix,
        num_assets=num_assets,
        num_clusters=request.num_clusters,
    )
    result, solver_metadata, backend_mode = solve_finance_quadratic_program(
        application.to_quadratic_program(),
        solver=request.solver,
        optimizer_config=request.optimizer,
        reps=request.reps,
        shots=request.shots,
        seed=request.seed,
    )

    selected_asset_indices = [int(index) for index in application.interpret(result)]
    selected_assets = None
    if request.asset_labels is not None:
        selected_assets = [request.asset_labels[index] for index in selected_asset_indices]

    return {
        "selected_asset_indices": selected_asset_indices,
        "selected_assets": selected_assets,
        "objective_value": float(result.fval),
        "constraint_summary": {
            "num_assets": num_assets,
            "num_clusters": request.num_clusters,
            "selected_count": len(selected_asset_indices),
        },
        "solver_metadata": solver_metadata,
        "provider": "qiskit-finance",
        "backend_mode": backend_mode,
    }
