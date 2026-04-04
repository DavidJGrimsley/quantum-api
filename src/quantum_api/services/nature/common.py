from __future__ import annotations

from typing import Any

from quantum_api.models.nature import NatureProblemRequest
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def build_problem_and_operator(request: NatureProblemRequest) -> tuple[Any, Any]:
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
    return problem, operator
