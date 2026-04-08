from __future__ import annotations

from typing import Any

from quantum_api.ibm_credentials import ResolvedIbmCredentials
from quantum_api.models.api import (
    QasmExportRequest,
    QasmImportRequest,
    QasmRunRequest,
    TranspileRequest,
)
from quantum_api.services.backend_catalog import resolve_backend
from quantum_api.services.circuit_conversion import (
    build_circuit_from_definition,
    export_qasm,
    normalize_operations,
    parse_qasm,
)
from quantum_api.services.circuit_runner import normalize_counts, serialize_statevector
from quantum_api.services.quantum_runtime import runtime


def transpile_circuit(
    request: TranspileRequest,
    *,
    ibm_credentials: ResolvedIbmCredentials | None = None,
) -> dict[str, object]:
    if not runtime.qiskit_available:
        raise RuntimeError("qiskit is unavailable for transpilation")

    if request.circuit is not None:
        source_circuit = build_circuit_from_definition(request.circuit)
        input_format = "circuit"
    else:
        assert request.qasm is not None
        source_circuit, _ = parse_qasm(
            source=request.qasm.source,
            qasm_version=request.qasm.qasm_version,
        )
        input_format = "qasm"

    provider, backend = resolve_backend(
        backend_name=request.backend_name,
        provider=request.provider,
        ibm_credentials=ibm_credentials,
    )
    transpiled = _run_transpile(
        source_circuit,
        backend=backend,
        optimization_level=request.optimization_level,
        seed_transpiler=request.seed_transpiler,
    )

    qasm_output = export_qasm(transpiled, request.output_qasm_version)
    return {
        "backend_name": request.backend_name,
        "provider": provider,
        "input_format": input_format,
        "num_qubits": int(transpiled.num_qubits),
        "depth": int(transpiled.depth() or 0),
        "size": int(transpiled.size() or 0),
        "operations": normalize_operations(transpiled),
        "qasm_version": request.output_qasm_version,
        "qasm": qasm_output,
    }


def import_qasm(request: QasmImportRequest) -> dict[str, object]:
    if not runtime.qiskit_available:
        raise RuntimeError("qiskit is unavailable for QASM import")

    circuit, detected_qasm_version = parse_qasm(
        source=request.qasm,
        qasm_version=request.qasm_version,
    )
    return {
        "detected_qasm_version": detected_qasm_version,
        "num_qubits": int(circuit.num_qubits),
        "depth": int(circuit.depth() or 0),
        "size": int(circuit.size() or 0),
        "operations": normalize_operations(circuit),
    }


def export_circuit_to_qasm(request: QasmExportRequest) -> dict[str, object]:
    if not runtime.qiskit_available:
        raise RuntimeError("qiskit is unavailable for QASM export")

    circuit = build_circuit_from_definition(request.circuit)
    qasm_text = export_qasm(circuit, request.qasm_version)
    return {
        "qasm_version": request.qasm_version,
        "qasm": qasm_text,
        "num_qubits": int(circuit.num_qubits),
        "depth": int(circuit.depth() or 0),
        "size": int(circuit.size() or 0),
    }


def run_qasm(request: QasmRunRequest) -> dict[str, object]:
    if not runtime.qiskit_available or runtime.AerSimulator is None or runtime.transpile is None:
        raise RuntimeError("qiskit is unavailable for QASM execution")

    circuit, detected_qasm_version = parse_qasm(
        source=request.qasm,
        qasm_version=request.qasm_version,
    )
    num_qubits = int(circuit.num_qubits)
    aer_simulator = runtime.AerSimulator
    transpile_fn = runtime.transpile

    payload: dict[str, object] = {
        "detected_qasm_version": detected_qasm_version,
        "num_qubits": num_qubits,
        "shots": request.shots,
        "counts": None,
        "backend_mode": "qiskit",
        "statevector": None,
    }

    if request.shots is not None:
        sampling_backend = aer_simulator()
        sampling_circuit = circuit.copy()
        has_measurements = any(
            str(instruction.operation.name) == "measure"
            for instruction in sampling_circuit.data
        )
        if not has_measurements:
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
        payload["counts"] = normalize_counts(sampling_result.get_counts(), num_qubits)

    if request.include_statevector or request.shots is None:
        statevector_backend = aer_simulator(method="statevector")
        statevector_circuit = circuit.copy()
        if hasattr(statevector_circuit, "remove_final_measurements"):
            statevector_circuit = statevector_circuit.remove_final_measurements(inplace=False)
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
        payload["statevector"] = serialize_statevector(statevector_result.get_statevector())

    return payload


def _run_transpile(
    circuit: Any,
    *,
    backend: Any,
    optimization_level: int,
    seed_transpiler: int | None,
) -> Any:
    assert runtime.transpile is not None
    return runtime.transpile(
        circuit,
        backend,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )
