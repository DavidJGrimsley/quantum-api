import math

import pytest

from quantum_api.config import get_settings
from quantum_api.services.quantum_runtime import runtime

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)


def _bell_payload(*, include_statevector: bool = False, seed: int | None = 7) -> dict[str, object]:
    return {
        "num_qubits": 2,
        "operations": [
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
        ],
        "shots": 1024,
        "include_statevector": include_statevector,
        "seed": seed,
    }


@requires_qiskit
def test_circuits_run_bell_contract(client):
    response = client.post("/v1/circuits/run", json=_bell_payload())
    assert response.status_code == 200

    payload = response.json()
    assert payload["num_qubits"] == 2
    assert payload["shots"] == 1024
    assert payload["backend_mode"] == "qiskit"
    assert payload["statevector"] is None
    assert sum(payload["counts"].values()) == payload["shots"]
    assert all(len(bitstring) == payload["num_qubits"] for bitstring in payload["counts"])
    assert set(payload["counts"].keys()).issubset({"00", "11"})


@requires_qiskit
def test_circuits_run_ghz_contract(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 3,
            "operations": [
                {"gate": "h", "target": 0},
                {"gate": "cx", "control": 0, "target": 1},
                {"gate": "cx", "control": 1, "target": 2},
            ],
            "shots": 512,
            "seed": 13,
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert sum(payload["counts"].values()) == payload["shots"]
    assert all(len(bitstring) == payload["num_qubits"] for bitstring in payload["counts"])
    assert set(payload["counts"].keys()).issubset({"000", "111"})


@requires_qiskit
def test_circuits_run_rotation_contract(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 1,
            "operations": [{"gate": "ry", "target": 0, "theta": math.pi / 2}],
            "shots": 400,
            "seed": 21,
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["num_qubits"] == 1
    assert sum(payload["counts"].values()) == 400
    assert set(payload["counts"].keys()).issubset({"0", "1"})


@requires_qiskit
def test_circuits_run_with_statevector_returns_amplitudes(client):
    response = client.post("/v1/circuits/run", json=_bell_payload(include_statevector=True))
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload["statevector"], list)
    assert len(payload["statevector"]) == 4
    for amplitude in payload["statevector"]:
        assert set(amplitude.keys()) == {"real", "imag"}


def test_circuits_run_returns_503_when_qiskit_unavailable(client):
    old_value = runtime.qiskit_available
    runtime.qiskit_available = False
    try:
        response = client.post("/v1/circuits/run", json=_bell_payload())
        assert response.status_code == 503
    finally:
        runtime.qiskit_available = old_value


def test_circuits_run_validation_invalid_gate(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 1,
            "operations": [{"gate": "invalid", "target": 0}],
            "shots": 10,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_invalid_qubit_index(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 2,
            "operations": [{"gate": "x", "target": 2}],
            "shots": 10,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_invalid_shots(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 1,
            "operations": [{"gate": "x", "target": 0}],
            "shots": get_settings().max_circuit_shots + 1,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_num_qubits_limit(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": get_settings().max_circuit_qubits + 1,
            "operations": [{"gate": "x", "target": 0}],
            "shots": 10,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_depth_limit(client):
    max_depth = get_settings().max_circuit_depth
    operations = [{"gate": "x", "target": 0}] * (max_depth + 1)
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 1,
            "operations": operations,
            "shots": 10,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_invalid_gate_parameter_combo(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 2,
            "operations": [{"gate": "cx", "target": 1}],
            "shots": 10,
        },
    )
    assert response.status_code == 422


def test_circuits_run_validation_control_must_differ_from_target(client):
    response = client.post(
        "/v1/circuits/run",
        json={
            "num_qubits": 2,
            "operations": [{"gate": "cx", "control": 1, "target": 1}],
            "shots": 10,
        },
    )
    assert response.status_code == 422
