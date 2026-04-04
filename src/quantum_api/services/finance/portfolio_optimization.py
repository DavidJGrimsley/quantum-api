from __future__ import annotations

from typing import Any

import numpy as np

from quantum_api.models.finance import FinancePortfolioOptimizationRequest
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.qiskit_common.serialization import bitstring_from_vector
from quantum_api.services.quantum_runtime import runtime


def solve_portfolio_optimization(request: FinancePortfolioOptimizationRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_finance_available,
        provider="qiskit-finance",
        import_error=runtime.qiskit_finance_import_error,
    )
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )
    ensure_dependency(
        available=runtime.qiskit_optimization_available,
        provider="qiskit-optimization",
        import_error=runtime.qiskit_optimization_import_error,
    )

    from qiskit.primitives import StatevectorSampler
    from qiskit_algorithms.minimum_eigensolvers import QAOA, NumPyMinimumEigensolver
    from qiskit_finance.applications import PortfolioOptimization
    from qiskit_optimization.algorithms import MinimumEigenOptimizer

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
    program = application.to_quadratic_program()

    if request.solver == "exact":
        min_eigen_solver = NumPyMinimumEigensolver()
        backend_mode = "numpy_minimum_eigensolver"
        optimizer_metadata: dict[str, object] = {
            "solver": "exact",
            "optimizer": None,
        }
    else:
        optimizer = build_optimizer(request.optimizer)
        min_eigen_solver = QAOA(
            sampler=StatevectorSampler(default_shots=request.shots, seed=request.seed),
            optimizer=optimizer,
            reps=request.reps,
        )
        backend_mode = "statevector_sampler"
        optimizer_metadata = optimizer_metadata_from_result(
            name=request.optimizer.name,
            maxiter=request.optimizer.maxiter,
            result=min_eigen_solver,
        ).model_dump(mode="json")

    result = MinimumEigenOptimizer(min_eigen_solver).solve(program)
    raw_metadata: dict[str, Any] = {
        "solver": request.solver,
        "best_bitstring": bitstring_from_vector(result.x),
    }
    if request.solver == "qaoa":
        raw_metadata["optimizer"] = optimizer_metadata_from_result(
            name=request.optimizer.name,
            maxiter=request.optimizer.maxiter,
            result=result.min_eigen_solver_result,
        ).model_dump(mode="json")
    else:
        raw_metadata.update(optimizer_metadata)

    selected_allocation = [int(round(float(item))) for item in result.x]
    return {
        "selected_allocation": selected_allocation,
        "objective_value": float(result.fval),
        "constraint_summary": {
            "budget": request.budget,
            "selected_count": sum(selected_allocation),
        },
        "solver_metadata": raw_metadata,
        "provider": "qiskit-finance",
        "backend_mode": backend_mode,
    }
