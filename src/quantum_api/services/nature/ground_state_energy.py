from __future__ import annotations

from quantum_api.models.nature import NatureGroundStateEnergyRequest
from quantum_api.services.nature.common import build_problem_and_operator
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def compute_ground_state_energy(request: NatureGroundStateEnergyRequest) -> dict[str, object]:
    from qiskit.circuit.library import real_amplitudes
    from qiskit.primitives import StatevectorEstimator
    from qiskit_algorithms.minimum_eigensolvers import VQE
    from qiskit_algorithms.utils import algorithm_globals

    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    problem, operator = build_problem_and_operator(request)
    optimizer = build_optimizer(request.optimizer)
    if request.seed is not None:
        algorithm_globals.random_seed = request.seed
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
    interpreted = problem.interpret(result)
    total_energy = None
    if getattr(interpreted, "total_energies", None) is not None:
        total_energies = list(interpreted.total_energies)
        if total_energies:
            total_energy = float(total_energies[0])

    return {
        "ground_state_energy": float(interpreted.groundenergy),
        "total_energy": total_energy,
        "nuclear_repulsion_energy": (
            float(problem.nuclear_repulsion_energy)
            if problem.nuclear_repulsion_energy is not None
            else None
        ),
        "mapped_problem_summary": {
            "mapper": request.mapper,
            "num_qubits": int(operator.num_qubits),
            "num_spatial_orbitals": int(problem.num_spatial_orbitals),
            "num_particles": [int(value) for value in problem.num_particles],
        },
        "solver_metadata": {
            "optimizer": optimizer_metadata_from_result(
                name=request.optimizer.name,
                maxiter=request.optimizer.maxiter,
                result=result,
            ).model_dump(mode="json"),
            "electronic_energy": float(result.eigenvalue.real),
            "basis": request.basis,
        },
        "provider": "qiskit-nature",
        "backend_mode": "statevector_estimator",
    }
