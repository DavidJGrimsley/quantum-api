from __future__ import annotations

from collections.abc import Sequence

from quantum_api.models.qiskit_common import PauliTerm
from quantum_api.services.service_errors import QuantumApiServiceError


def sparse_pauli_op_from_terms(terms: Sequence[PauliTerm]) -> object:
    from qiskit.quantum_info import SparsePauliOp

    normalized_terms: list[tuple[str, float]] = []
    qubit_count: int | None = None
    for term in terms:
        pauli = term.pauli.strip().upper()
        if not pauli or any(symbol not in {"I", "X", "Y", "Z"} for symbol in pauli):
            raise QuantumApiServiceError(
                error="invalid_pauli_term",
                message=f"Invalid Pauli string '{term.pauli}'.",
                status_code=400,
                details={"pauli": term.pauli},
            )
        if qubit_count is None:
            qubit_count = len(pauli)
        elif len(pauli) != qubit_count:
            raise QuantumApiServiceError(
                error="invalid_pauli_term",
                message="All Pauli strings must have the same length.",
                status_code=400,
            )
        normalized_terms.append((pauli, float(term.coefficient)))
    return SparsePauliOp.from_list(normalized_terms)
