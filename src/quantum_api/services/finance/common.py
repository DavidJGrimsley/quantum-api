from __future__ import annotations

from typing import Any

from quantum_api.models.finance import FinanceSolver
from quantum_api.models.qiskit_common import OptimizerConfig
from quantum_api.services.qiskit_common.algorithm_seed import scoped_algorithm_seed
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.qiskit_common.serialization import bitstring_from_vector
from quantum_api.services.quantum_runtime import runtime


def solve_finance_quadratic_program(
    program: Any,
    *,
    solver: FinanceSolver,
    optimizer_config: OptimizerConfig,
    reps: int,
    shots: int,
    seed: int | None,
) -> tuple[Any, dict[str, object], str]:
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
    from qiskit_optimization.algorithms import MinimumEigenOptimizer

    with scoped_algorithm_seed(seed):
        if solver == "exact":
            min_eigen_solver = NumPyMinimumEigensolver()
            backend_mode = "numpy_minimum_eigensolver"
        else:
            min_eigen_solver = QAOA(
                sampler=StatevectorSampler(default_shots=shots, seed=seed),
                optimizer=build_optimizer(optimizer_config),
                reps=reps,
            )
            backend_mode = "statevector_sampler"

        result = MinimumEigenOptimizer(min_eigen_solver).solve(program)

    solver_metadata: dict[str, object] = {
        "solver": solver,
        "best_bitstring": bitstring_from_vector(result.x),
        "optimizer": None,
    }
    if solver == "qaoa":
        solver_metadata["optimizer"] = optimizer_metadata_from_result(
            name=optimizer_config.name,
            maxiter=optimizer_config.maxiter,
            result=result.min_eigen_solver_result,
        ).model_dump(mode="json")

    return result, solver_metadata, backend_mode
