from __future__ import annotations

from quantum_api.models.optimization import OptimizationKnapsackRequest
from quantum_api.services.optimization.common import solve_quadratic_program


def solve_knapsack(request: OptimizationKnapsackRequest) -> dict[str, object]:
    from qiskit_optimization.applications import Knapsack

    application = Knapsack(request.item_values, request.item_weights, request.capacity)
    result, solver_metadata, backend_mode = solve_quadratic_program(
        application.to_quadratic_program(),
        solver=request.solver,
        optimizer_config=request.optimizer,
        reps=request.reps,
        shots=request.shots,
        seed=request.seed,
    )

    selected_items = [int(index) for index in application.interpret(result)]
    return {
        "selected_items": selected_items,
        "total_value": int(sum(request.item_values[index] for index in selected_items)),
        "total_weight": int(sum(request.item_weights[index] for index in selected_items)),
        "solver_metadata": solver_metadata,
        "provider": "qiskit-optimization",
        "backend_mode": backend_mode,
    }
