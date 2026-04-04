from __future__ import annotations

import networkx as nx

from quantum_api.models.optimization import OptimizationMaxcutRequest
from quantum_api.services.optimization.common import solve_quadratic_program


def solve_maxcut(request: OptimizationMaxcutRequest) -> dict[str, object]:
    from qiskit_optimization.applications import Maxcut

    graph = nx.Graph()
    graph.add_nodes_from(range(request.num_nodes))
    for edge in request.edges:
        graph.add_edge(edge.source, edge.target, weight=float(edge.weight))

    application = Maxcut(graph)
    result, solver_metadata, backend_mode = solve_quadratic_program(
        application.to_quadratic_program(),
        solver=request.solver,
        optimizer_config=request.optimizer,
        reps=request.reps,
        shots=request.shots,
        seed=request.seed,
    )

    partition = sorted(
        ([int(node) for node in group] for group in application.interpret(result)),
        key=lambda group: (group[0] if group else -1, len(group)),
    )
    return {
        "partition": partition,
        "cut_value": float(result.fval),
        "bitstring": solver_metadata["best_bitstring"],
        "solver_metadata": solver_metadata,
        "provider": "qiskit-optimization",
        "backend_mode": backend_mode,
    }
