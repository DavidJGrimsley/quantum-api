from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from quantum_api.models.algorithms import NamedPauliSum
from quantum_api.models.core import CircuitDefinition
from quantum_api.services.circuit_conversion import (
    build_circuit_from_definition,
    normalize_operations,
)
from quantum_api.services.qiskit_common.operators import sparse_pauli_op_from_terms
from quantum_api.services.qiskit_common.serialization import (
    amplitudes_payload,
    complex_payload,
    float_pair_payload,
    json_safe_value,
)


def build_circuit(definition: CircuitDefinition | None) -> Any | None:
    if definition is None:
        return None
    return build_circuit_from_definition(definition)


def build_sampler(*, shots: int, seed: int | None) -> Any:
    from qiskit.primitives import StatevectorSampler

    return StatevectorSampler(default_shots=shots, seed=seed)


def build_estimator(*, seed: int | None) -> Any:
    from qiskit.primitives import StatevectorEstimator

    return StatevectorEstimator(seed=seed)


def build_marked_state_oracle(marked_bitstrings: Sequence[str]) -> Any:
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import Diagonal

    num_qubits = len(marked_bitstrings[0])
    phases = [1.0] * (2 ** num_qubits)
    for bitstring in marked_bitstrings:
        phases[int(bitstring, 2)] = -1.0
    oracle = QuantumCircuit(num_qubits)
    oracle.append(Diagonal(phases), range(num_qubits))
    return oracle


def distribution_to_counts(distribution: dict[str, float] | None, *, shots: int) -> dict[str, int]:
    if not distribution:
        return {}
    raw_counts = {key: int(round(float(value) * shots)) for key, value in distribution.items()}
    total = sum(raw_counts.values())
    if total != shots:
        top_key = max(distribution, key=distribution.get)
        raw_counts[top_key] = raw_counts.get(top_key, 0) + (shots - total)
    return raw_counts


def serialize_distribution(distribution: dict[str, Any] | None) -> dict[str, float] | None:
    if distribution is None:
        return None
    return {str(key): float(value) for key, value in distribution.items()}


def serialize_confidence_interval(value: Any) -> list[float] | None:
    return float_pair_payload(value)


def serialize_samples(value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(float(key)): float(probability) for key, probability in value.items()}
    return None


def serialize_evolved_state(circuit: Any) -> tuple[list[dict[str, object]], list[dict[str, float]]]:
    from qiskit.quantum_info import Statevector

    operations = normalize_operations(circuit)
    statevector = Statevector.from_instruction(circuit)
    return operations, amplitudes_payload(statevector.data)


def build_aux_operators(aux_operators: Sequence[NamedPauliSum] | None) -> tuple[list[Any] | None, list[str] | None]:
    if aux_operators is None:
        return None, None
    operators = [sparse_pauli_op_from_terms(item.pauli_sum) for item in aux_operators]
    names = [item.name for item in aux_operators]
    return operators, names


def serialize_aux_operator_values(value: Any, names: Sequence[str] | None) -> list[dict[str, object]] | None:
    if value is None or names is None:
        return None

    payload: list[dict[str, object]] = []
    items = list(value) if isinstance(value, Iterable) else [value]
    for index, item in enumerate(items):
        if isinstance(item, tuple) and len(item) == 2:
            scalar, metadata = item
        else:
            scalar, metadata = item, None
        payload.append(
            {
                "name": names[index] if index < len(names) else f"aux_{index}",
                "value": complex_payload(complex(scalar)),
                "metadata": json_safe_value(metadata) if isinstance(metadata, dict) else None,
            }
        )
    return payload
