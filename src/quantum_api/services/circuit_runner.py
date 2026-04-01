from __future__ import annotations

from typing import Any

from quantum_api.models.api import CircuitOperation, CircuitRunRequest
from quantum_api.services.quantum_runtime import runtime


def _build_circuit(num_qubits: int, operations: list[CircuitOperation]) -> Any:
    circuit_class = runtime.QuantumCircuit
    if circuit_class is None:
        raise RuntimeError("qiskit QuantumCircuit is unavailable")
    circuit = circuit_class(num_qubits)
    for operation in operations:
        if operation.gate == "x":
            circuit.x(operation.target)
        elif operation.gate == "z":
            circuit.z(operation.target)
        elif operation.gate == "h":
            circuit.h(operation.target)
        elif operation.gate == "ry":
            circuit.ry(operation.theta, operation.target)
        elif operation.gate == "cx":
            circuit.cx(operation.control, operation.target)
    return circuit


def _normalize_counts(raw_counts: dict[str, int], num_qubits: int) -> dict[str, int]:
    normalized_counts = {str(key).zfill(num_qubits): int(value) for key, value in raw_counts.items()}
    return dict(sorted(normalized_counts.items()))


def _serialize_statevector(statevector: Any) -> list[dict[str, float]]:
    raw_values = getattr(statevector, "data", statevector)
    amplitudes: list[dict[str, float]] = []
    for value in raw_values:
        complex_value = complex(value)
        amplitudes.append(
            {
                "real": float(complex_value.real),
                "imag": float(complex_value.imag),
            }
        )
    return amplitudes


def run_circuit(request: CircuitRunRequest) -> dict[str, object]:
    if not runtime.qiskit_available or runtime.AerSimulator is None or runtime.transpile is None:
        raise RuntimeError("qiskit is unavailable for circuit execution")

    aer_simulator = runtime.AerSimulator
    transpile_fn = runtime.transpile

    base_circuit = _build_circuit(request.num_qubits, request.operations)
    sampling_backend = aer_simulator()
    sampling_circuit = base_circuit.copy()
    sampling_circuit.measure_all()

    sampling_transpiled = transpile_fn(
        sampling_circuit,
        sampling_backend,
        seed_transpiler=request.seed,
    )
    sampling_run_kwargs: dict[str, object] = {"shots": request.shots}
    if request.seed is not None:
        sampling_run_kwargs["seed_simulator"] = request.seed
    sampling_result = sampling_backend.run(sampling_transpiled, **sampling_run_kwargs).result()

    payload: dict[str, object] = {
        "num_qubits": request.num_qubits,
        "shots": request.shots,
        "counts": _normalize_counts(sampling_result.get_counts(), request.num_qubits),
        "backend_mode": "qiskit",
        "statevector": None,
    }

    if request.include_statevector:
        statevector_backend = aer_simulator(method="statevector")
        statevector_circuit = base_circuit.copy()
        statevector_circuit.save_statevector()
        statevector_transpiled = transpile_fn(
            statevector_circuit,
            statevector_backend,
            seed_transpiler=request.seed,
        )
        statevector_run_kwargs: dict[str, object] = {"shots": 1}
        if request.seed is not None:
            statevector_run_kwargs["seed_simulator"] = request.seed
        statevector_result = statevector_backend.run(
            statevector_transpiled,
            **statevector_run_kwargs,
        ).result()
        payload["statevector"] = _serialize_statevector(statevector_result.get_statevector())

    return payload
