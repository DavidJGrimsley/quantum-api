from __future__ import annotations

from quantum_api.models.algorithms import PhaseEstimationRequest
from quantum_api.services.algorithms.common import (
    build_circuit,
    build_sampler,
    serialize_distribution,
)
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.operators import sparse_pauli_op_from_terms
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.service_errors import QuantumApiServiceError


def run_phase_estimation(request: PhaseEstimationRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit_algorithms import (
        HamiltonianPhaseEstimation,
        IterativePhaseEstimation,
        PhaseEstimation,
    )

    sampler = build_sampler(shots=request.shots, seed=request.seed)
    state_preparation = build_circuit(request.state_preparation)

    if request.variant == "standard":
        result = PhaseEstimation(
            num_evaluation_qubits=request.num_evaluation_qubits,
            sampler=sampler,
        ).estimate(
            build_circuit(request.unitary),
            state_preparation=state_preparation,
        )
        phase_distribution = serialize_distribution(getattr(result, "phases", None))
        estimated_eigenvalue = None
    elif request.variant == "iterative":
        result = IterativePhaseEstimation(
            num_iterations=request.num_iterations,
            sampler=sampler,
        ).estimate(
            build_circuit(request.unitary),
            state_preparation=state_preparation,
        )
        phase_distribution = None
        estimated_eigenvalue = None
    else:
        if not request.hamiltonian:
            raise QuantumApiServiceError(
                error="invalid_hamiltonian",
                message="hamiltonian must contain at least one Pauli term for variant 'hamiltonian'.",
                status_code=400,
            )
        result = HamiltonianPhaseEstimation(
            num_evaluation_qubits=request.num_evaluation_qubits,
            sampler=sampler,
        ).estimate(
            sparse_pauli_op_from_terms(request.hamiltonian),
            state_preparation=state_preparation,
            bound=request.bound,
        )
        phase_distribution = None
        estimated_eigenvalue = float(result.most_likely_eigenvalue)

    return {
        "most_likely_phase": float(result.phase),
        "phase_distribution": phase_distribution,
        "estimated_eigenvalue": estimated_eigenvalue,
        "variant": request.variant,
        "provider": "qiskit-algorithms",
        "backend_mode": "statevector_sampler",
    }
