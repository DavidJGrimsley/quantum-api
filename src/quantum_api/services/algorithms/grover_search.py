from __future__ import annotations

from quantum_api.models.algorithms import GroverSearchRequest
from quantum_api.services.algorithms.common import (
    build_circuit,
    build_marked_state_oracle,
    build_sampler,
    distribution_to_counts,
)
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def run_grover_search(request: GroverSearchRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit_algorithms import AmplificationProblem, Grover

    if request.marked_bitstrings is not None:
        oracle = build_marked_state_oracle(request.marked_bitstrings)
        good_states = request.good_state_bitstrings or request.marked_bitstrings
        oracle_summary = {
            "mode": "marked_bitstrings",
            "num_qubits": len(request.marked_bitstrings[0]),
            "marked_state_count": len(request.marked_bitstrings),
        }
    else:
        oracle = build_circuit(request.oracle_circuit)
        good_states = request.good_state_bitstrings
        oracle_summary = {
            "mode": "oracle_circuit",
            "num_qubits": request.oracle_circuit.num_qubits,
            "marked_state_count": len(request.good_state_bitstrings or []),
        }

    problem = AmplificationProblem(
        oracle=oracle,
        state_preparation=build_circuit(request.state_preparation),
        objective_qubits=request.objective_qubits,
        is_good_state=good_states,
    )
    result = Grover(
        iterations=request.iterations,
        sample_from_iterations=request.sample_from_iterations,
        sampler=build_sampler(shots=request.shots, seed=request.seed),
    ).amplify(problem)

    distribution = result.circuit_results[-1] if result.circuit_results else {}
    return {
        "top_measurement": str(result.top_measurement),
        "counts": distribution_to_counts(distribution, shots=request.shots),
        "iterations_used": [int(item) for item in result.iterations],
        "good_state_found": bool(result.oracle_evaluation),
        "oracle_summary": oracle_summary,
        "provider": "qiskit-algorithms",
        "backend_mode": "statevector_sampler",
    }
