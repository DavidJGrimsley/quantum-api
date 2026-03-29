from __future__ import annotations

import re
from numbers import Integral, Real
from typing import Any

from quantum_api.models.api import (
    CircuitDefinition,
    CircuitOperation,
    OutputQasmVersion,
    QasmVersion,
)
from quantum_api.services.phase2_errors import Qasm3DependencyMissingError, QasmParseError
from quantum_api.services.quantum_runtime import runtime


def build_circuit_from_definition(definition: CircuitDefinition) -> Any:
    if not runtime.qiskit_available or runtime.QuantumCircuit is None:
        raise RuntimeError("qiskit is unavailable for circuit conversion")

    circuit = runtime.QuantumCircuit(definition.num_qubits)
    for operation in definition.operations:
        _apply_operation(circuit, operation)
    return circuit


def _apply_operation(circuit: Any, operation: CircuitOperation) -> None:
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


def normalize_operations(circuit: Any) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for instruction in circuit.data:
        gate_name = str(instruction.operation.name)
        qubits = [int(circuit.find_bit(qubit).index) for qubit in instruction.qubits]
        clbits = [int(circuit.find_bit(clbit).index) for clbit in instruction.clbits]
        params = [_serialize_param(param) for param in instruction.operation.params]
        payload.append(
            {
                "gate": gate_name,
                "qubits": qubits,
                "clbits": clbits,
                "params": params,
            }
        )
    return payload


def _serialize_param(value: object) -> Real | str | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value)
    return str(value)


def parse_qasm(source: str, qasm_version: QasmVersion) -> tuple[Any, OutputQasmVersion]:
    if not runtime.qiskit_available:
        raise RuntimeError("qiskit is unavailable for QASM parsing")

    if qasm_version in {"2", "3"}:
        circuit = _parse_qasm_with_version(source, qasm_version)
        return circuit, qasm_version

    parse_order = ["3", "2"] if _detect_qasm_version_hint(source) == "3" else ["2", "3"]
    parser_errors: dict[str, str] = {}
    qasm3_dependency_missing = False

    for version in parse_order:
        try:
            circuit = _parse_qasm_with_version(source, version)
            return circuit, version
        except Qasm3DependencyMissingError:
            qasm3_dependency_missing = True
            parser_errors["3"] = "missing optional dependency qiskit_qasm3_import"
            if version == "3":
                break
        except QasmParseError as exc:
            parser_errors[version] = str(exc.details.get("parser_error", exc.message)) if exc.details else exc.message

    if qasm3_dependency_missing:
        raise Qasm3DependencyMissingError(details={"parser_errors": parser_errors})

    raise QasmParseError(
        message="Unable to parse QASM input.",
        details={"parser_errors": parser_errors},
    )


def _parse_qasm_with_version(source: str, qasm_version: OutputQasmVersion) -> Any:
    parser = runtime.qasm2.loads if qasm_version == "2" else runtime.qasm3.loads  # type: ignore[union-attr]
    try:
        return parser(source)
    except Exception as exc:
        if qasm_version == "3" and _is_qasm3_dependency_error(exc):
            raise Qasm3DependencyMissingError(
                details={"parser_error": str(exc), "qasm_version": qasm_version},
            ) from exc
        raise QasmParseError(
            message=f"Failed to parse OpenQASM {qasm_version} input.",
            details={"parser_error": str(exc), "qasm_version": qasm_version},
        ) from exc


def _detect_qasm_version_hint(source: str) -> OutputQasmVersion:
    openqasm_header = re.search(r"OPENQASM\s+(\d+(?:\.\d+)?)", source, flags=re.IGNORECASE)
    if openqasm_header:
        version_token = openqasm_header.group(1).strip()
        if version_token.startswith("3"):
            return "3"
    return "2"


def export_qasm(circuit: Any, qasm_version: OutputQasmVersion) -> str:
    dumper = runtime.qasm2.dumps if qasm_version == "2" else runtime.qasm3.dumps  # type: ignore[union-attr]
    try:
        return str(dumper(circuit))
    except Exception as exc:
        if qasm_version == "3" and _is_qasm3_dependency_error(exc):
            raise Qasm3DependencyMissingError(
                details={"parser_error": str(exc), "qasm_version": qasm_version},
            ) from exc
        raise QasmParseError(
            message=f"Failed to export OpenQASM {qasm_version} output.",
            details={"parser_error": str(exc), "qasm_version": qasm_version},
        ) from exc


def _is_qasm3_dependency_error(exc: Exception) -> bool:
    return "qiskit_qasm3_import" in str(exc)
