from __future__ import annotations

import networkx as nx

from quantum_api.models.optimization import OptimizationTspRequest
from quantum_api.services.optimization.common import solve_quadratic_program


def _normalize_tour_order(order: list[int]) -> list[int]:
    if not order:
        return order

    size = len(order)
    min_index = min(range(size), key=order.__getitem__)
    rotated = order[min_index:] + order[:min_index]
    reversed_rotated = [rotated[0], *reversed(rotated[1:])]
    return min(rotated, reversed_rotated)


def solve_tsp(request: OptimizationTspRequest) -> dict[str, object]:
    from qiskit_optimization.applications import Tsp

    graph = nx.Graph()
    size = len(request.distance_matrix)
    graph.add_nodes_from(range(size))
    for source in range(size):
        for target in range(source + 1, size):
            graph.add_edge(source, target, weight=float(request.distance_matrix[source][target]))

    application = Tsp(graph)
    result, solver_metadata, backend_mode = solve_quadratic_program(
        application.to_quadratic_program(),
        solver=request.solver,
        optimizer_config=request.optimizer,
        reps=request.reps,
        shots=request.shots,
        seed=request.seed,
    )

    raw_order = application.interpret(result)
    tour_order = _normalize_tour_order([int(node) for node in raw_order])
    tour_length = sum(
        float(request.distance_matrix[tour_order[index]][tour_order[(index + 1) % len(tour_order)]])
        for index in range(len(tour_order))
    )
    return {
        "tour_order": tour_order,
        "tour_length": tour_length,
        "solver_metadata": solver_metadata,
        "provider": "qiskit-optimization",
        "backend_mode": backend_mode,
    }
