from __future__ import annotations

from quantum_api.models.phase5 import NatureGroundStateEnergyRequest
from quantum_api.services.phase5_common import (
    build_optimizer,
    ensure_dependency,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def compute_ground_state_energy(request: NatureGroundStateEnergyRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_nature_available,
        provider="qiskit-nature",
        import_error=runtime.qiskit_nature_import_error,
    )
    ensure_dependency(
        available=runtime.pyscf_available,
        provider="pyscf",
        import_error=runtime.pyscf_import_error,
    )
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit.circuit.library import real_amplitudes
    from qiskit.primitives import StatevectorEstimator
    from qiskit_algorithms.minimum_eigensolvers import VQE
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper
    from qiskit_nature.units import DistanceUnit

    atom_spec = "; ".join(
        f"{atom.symbol} {atom.x} {atom.y} {atom.z}"
        for atom in request.atoms
    )
    driver = PySCFDriver(
        atom=atom_spec,
        unit=DistanceUnit.ANGSTROM,
        charge=request.charge,
        spin=request.spin,
        basis=request.basis,
    )
    problem = driver.run()
    mapper = (
        ParityMapper(num_particles=problem.num_particles)
        if request.mapper == "parity"
        else JordanWignerMapper()
    )
    operator = mapper.map(problem.hamiltonian.second_q_op())
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
