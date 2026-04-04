from __future__ import annotations

from typing import Any

from quantum_api.models.optimization import OptimizationVqeRequest
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def sparse_pauli_from_request(request: OptimizationVqeRequest) -> Any:
    from qiskit.quantum_info import SparsePauliOp

    normalized_terms: list[tuple[str, float]] = []
    qubit_count: int | None = None
    for term in request.pauli_sum:
        pauli = term.pauli.strip().upper()
        if not pauli or any(symbol not in {"I", "X", "Y", "Z"} for symbol in pauli):
            raise Phase2ServiceError(
                error="invalid_pauli_term",
                message=f"Invalid Pauli string '{term.pauli}'.",
                status_code=400,
                details={"pauli": term.pauli},
            )
        if qubit_count is None:
            qubit_count = len(pauli)
        elif len(pauli) != qubit_count:
            raise Phase2ServiceError(
                error="invalid_pauli_term",
                message="All Pauli strings must have the same length.",
                status_code=400,
            )
        normalized_terms.append((pauli, float(term.coefficient)))
    assert qubit_count is not None
    return SparsePauliOp.from_list(normalized_terms)


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
