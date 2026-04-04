from __future__ import annotations

from quantum_api.models.nature import NatureFermionicMappingPreviewRequest
from quantum_api.services.nature.common import build_problem_and_operator
from quantum_api.services.qiskit_common.serialization import complex_payload


def preview_fermionic_mapping(request: NatureFermionicMappingPreviewRequest) -> dict[str, object]:
    problem, operator = build_problem_and_operator(request)
    fermionic_operator = problem.hamiltonian.second_q_op()
    preview_terms = [
        {
            "pauli": pauli,
            "coefficient": complex_payload(complex(coefficient)),
        }
        for pauli, coefficient in list(zip(operator.paulis.to_labels(), operator.coeffs, strict=True))[:8]
    ]
    return {
        "mapped_problem_summary": {
            "mapper": request.mapper,
            "num_qubits": int(operator.num_qubits),
            "num_spatial_orbitals": int(problem.num_spatial_orbitals),
            "num_particles": [int(value) for value in problem.num_particles],
            "fermionic_term_count": int(len(fermionic_operator)),
            "mapped_term_count": int(len(operator)),
        },
        "preview_terms": preview_terms,
        "provider": "qiskit-nature",
        "backend_mode": "mapping_preview",
    }
