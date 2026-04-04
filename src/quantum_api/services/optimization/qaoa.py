from __future__ import annotations

from typing import Any

from quantum_api.models.optimization import (
    BinaryQuadraticProblem,
    OptimizationQaoaRequest,
    OptimizationSolutionSample,
)
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.qiskit_common.serialization import bitstring_from_vector
from quantum_api.services.quantum_runtime import runtime


def quadratic_program_from_problem(problem: BinaryQuadraticProblem) -> Any:
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
    from qiskit_algorithms.utils import algorithm_globals
    from qiskit_optimization.algorithms import MinimumEigenOptimizer

    program = quadratic_program_from_problem(request.problem)
    optimizer = build_optimizer(request.optimizer)
    if request.seed is not None:
        algorithm_globals.random_seed = request.seed
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
