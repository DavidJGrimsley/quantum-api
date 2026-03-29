from __future__ import annotations

import pytest

from quantum_api.services.quantum_runtime import runtime

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)

QASM2_SINGLE_QUBIT = (
    'OPENQASM 2.0; include "qelib1.inc"; '
    "qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];"
)


@requires_qiskit
def test_qasm_import_qasm2_contract(client):
    response = client.post(
        "/v1/qasm/import",
        json={
            "qasm": QASM2_SINGLE_QUBIT,
            "qasm_version": "auto",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["detected_qasm_version"] == "2"
    assert payload["num_qubits"] == 1
    assert payload["depth"] >= 1
    assert payload["size"] >= 1
    assert isinstance(payload["operations"], list)
    assert any(operation["gate"] == "h" for operation in payload["operations"])


@requires_qiskit
def test_qasm_export_defaults_to_qasm3(client):
    response = client.post(
        "/v1/qasm/export",
        json={
            "circuit": {
                "num_qubits": 2,
                "operations": [
                    {"gate": "h", "target": 0},
                    {"gate": "cx", "control": 0, "target": 1},
                ],
            }
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["qasm_version"] == "3"
    assert "OPENQASM 3" in payload["qasm"]
    assert payload["num_qubits"] == 2


@requires_qiskit
def test_qasm_export_qasm2_option(client):
    response = client.post(
        "/v1/qasm/export",
        json={
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
            "qasm_version": "2",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["qasm_version"] == "2"
    assert payload["qasm"].startswith("OPENQASM 2.0;")


@requires_qiskit
def test_qasm_import_qasm3_dependency_missing_error_is_normalized(client, monkeypatch):
    def missing_qasm3_dependency(_source: str):
        raise RuntimeError("qiskit_qasm3_import is required for OpenQASM 3 import")

    monkeypatch.setattr(runtime.qasm3, "loads", missing_qasm3_dependency)

    response = client.post(
        "/v1/qasm/import",
        json={
            "qasm": 'OPENQASM 3.0; include "stdgates.inc"; qubit[1] q; h q[0];',
            "qasm_version": "3",
        },
    )
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "qasm3_dependency_missing"


def test_qasm_import_validation_invalid_qasm_version(client):
    response = client.post(
        "/v1/qasm/import",
        json={
            "qasm": QASM2_SINGLE_QUBIT,
            "qasm_version": "9",
        },
    )
    assert response.status_code == 422


def test_qasm_export_validation_missing_circuit(client):
    response = client.post("/v1/qasm/export", json={})
    assert response.status_code == 422
