from __future__ import annotations

from typing import Any

from quantum_api.models.phase5 import (
    OptimizationQaoaRequest,
    OptimizationSolutionSample,
    OptimizationVqeRequest,
)
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.phase5_common import (
    bitstring_from_vector,
    build_optimizer,
    ensure_dependency,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def _quadratic_program_from_problem(problem: Any) -> Any:
    from qiskit_optimization import QuadraticProgram

    program = QuadraticProgram()
    variable_names = problem.variable_names or [f"x{i}" for i in range(problem.num_variables)]
    for name in variable_names:
        program.binary_var(name)

    linear = {name: float(problem.linear[index]) for index, name in enumerate(variable_names)}
    quadratic = {
        (variable_names[term.i], variable_names[term.j]): float(term.value)
        for term in problem.quadratic
    }

    if problem.sense == "maximize":
        program.maximize(constant=float(problem.constant), linear=linear, quadratic=quadratic)
    else:
        program.minimize(constant=float(problem.constant), linear=linear, quadratic=quadratic)
    return program


def solve_qaoa(request: OptimizationQaoaRequest) -> dict[str, object]:
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
    from qiskit_algorithms.minimum_eigensolvers import QAOA
    from qiskit_optimization.algorithms import MinimumEigenOptimizer

    program = _quadratic_program_from_problem(request.problem)
    optimizer = build_optimizer(request.optimizer)
    min_eigen_solver = QAOA(
        sampler=StatevectorSampler(default_shots=request.shots, seed=request.seed),
        optimizer=optimizer,
        reps=request.reps,
    )
    result = MinimumEigenOptimizer(min_eigen_solver).solve(program)
    raw_solver_result = result.min_eigen_solver_result

    samples = [
        OptimizationSolutionSample(
            bitstring=bitstring_from_vector(sample.x),
            objective_value=float(sample.fval),
            probability=float(sample.probability),
            status=getattr(sample.status, "name", str(sample.status)),
        ).model_dump(mode="json")
        for sample in result.samples
    ]

    return {
        "best_bitstring": bitstring_from_vector(result.x),
        "objective_value": float(result.fval),
        "solution_samples": samples,
        "optimizer_metadata": optimizer_metadata_from_result(
            name=request.optimizer.name,
            maxiter=request.optimizer.maxiter,
            result=raw_solver_result,
        ).model_dump(mode="json"),
        "provider": "qiskit-algorithms",
        "backend_mode": "statevector_sampler",
        "warnings": None,
    }


def _sparse_pauli_from_request(request: OptimizationVqeRequest) -> Any:
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

    operator = _sparse_pauli_from_request(request)
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
