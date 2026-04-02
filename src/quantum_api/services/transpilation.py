from __future__ import annotations

from typing import Any

from quantum_api.ibm_credentials import ResolvedIbmCredentials
from quantum_api.models.api import QasmExportRequest, QasmImportRequest, TranspileRequest
from quantum_api.services.backend_catalog import resolve_backend
from quantum_api.services.circuit_conversion import (
    build_circuit_from_definition,
    export_qasm,
    normalize_operations,
    parse_qasm,
)
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
