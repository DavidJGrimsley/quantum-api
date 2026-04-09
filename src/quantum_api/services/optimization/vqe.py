from __future__ import annotations

from typing import Any

from quantum_api.models.optimization import OptimizationVqeRequest
from quantum_api.services.qiskit_common.algorithm_seed import scoped_algorithm_seed
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.operators import sparse_pauli_op_from_terms
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def sparse_pauli_from_request(request: OptimizationVqeRequest) -> Any:
    return sparse_pauli_op_from_terms(request.pauli_sum)


def solve_vqe(request: OptimizationVqeRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit.circuit.library import real_amplitudes
    from qiskit.primitives import StatevectorEstimator
    from qiskit_algorithms.minimum_eigensolvers import VQE

    operator = sparse_pauli_from_request(request)
    optimizer = build_optimizer(request.optimizer)

    with scoped_algorithm_seed(request.seed):
        ansatz = real_amplitudes(
            operator.num_qubits,
            reps=request.ansatz.reps,
            entanglement=request.ansatz.entanglement,
        )
        result = VQE(
            estimator=StatevectorEstimator(seed=request.seed),
            ansatz=ansatz,
            optimizer=optimizer,
        ).compute_minimum_eigenvalue(operator)

    return {
        "minimum_eigenvalue": float(result.eigenvalue.real),
        "optimal_parameters": [float(value) for value in result.optimal_point],
        "convergence": optimizer_metadata_from_result(
            name=request.optimizer.name,
            maxiter=request.optimizer.maxiter,
            result=result,
        ).model_dump(mode="json"),
        "provider": "qiskit-algorithms",
        "backend_mode": "statevector_estimator",
        "warnings": None,
    }
