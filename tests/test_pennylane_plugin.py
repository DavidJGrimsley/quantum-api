from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import pytest

SDK_PYTHON_PATH = Path(__file__).resolve().parents[1] / "sdk" / "python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.append(str(SDK_PYTHON_PATH))

SDK_PENNYLANE_PATH = Path(__file__).resolve().parents[1] / "sdk" / "pennylane"
if str(SDK_PENNYLANE_PATH) not in sys.path:
    sys.path.append(str(SDK_PENNYLANE_PATH))

qml = pytest.importorskip("pennylane")


def _quantum_api_device_class():
    from quantum_api_pennylane import QuantumApiDevice

    return QuantumApiDevice


class StubQuantumApiClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.payloads: list[dict[str, Any]] = []

    def run_qasm(self, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        del kwargs
        self.payloads.append(dict(payload))
        return dict(self.response)

    def close(self) -> None:
        return None


def test_quantum_api_device_counts_measurement_from_shots() -> None:
    stub = StubQuantumApiClient(
        {
            "detected_qasm_version": "2",
            "num_qubits": 1,
            "shots": 100,
            "counts": {"0": 52, "1": 48},
            "backend_mode": "qiskit",
            "statevector": None,
        }
    )

    QuantumApiDevice = _quantum_api_device_class()
    dev = QuantumApiDevice(wires=1, client=stub)

    @qml.set_shots(100)
    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(0)
        return qml.counts(wires=[0])

    result = circuit()

    assert result == {"0": 52, "1": 48}
    assert len(stub.payloads) == 1
    assert stub.payloads[0]["shots"] == 100
    assert stub.payloads[0]["include_statevector"] is False
    assert isinstance(stub.payloads[0]["qasm"], str)
    assert "OPENQASM 2.0" in stub.payloads[0]["qasm"]


def test_quantum_api_device_expval_reconstruction_from_counts() -> None:
    stub = StubQuantumApiClient(
        {
            "detected_qasm_version": "2",
            "num_qubits": 1,
            "shots": 100,
            "counts": {"0": 80, "1": 20},
            "backend_mode": "qiskit",
            "statevector": None,
        }
    )

    QuantumApiDevice = _quantum_api_device_class()
    dev = QuantumApiDevice(wires=1, client=stub)

    @qml.set_shots(100)
    @qml.qnode(dev)
    def circuit():
        return qml.expval(qml.PauliZ(0))

    result = circuit()

    assert float(result) == pytest.approx(0.6, abs=1e-9)
    assert len(stub.payloads) == 1
    assert stub.payloads[0]["include_statevector"] is False


def test_quantum_api_device_analytic_statevector_measurements() -> None:
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    stub = StubQuantumApiClient(
        {
            "detected_qasm_version": "2",
            "num_qubits": 1,
            "shots": None,
            "counts": None,
            "backend_mode": "qiskit",
            "statevector": [
                {"real": inv_sqrt2, "imag": 0.0},
                {"real": inv_sqrt2, "imag": 0.0},
            ],
        }
    )

    QuantumApiDevice = _quantum_api_device_class()
    dev = QuantumApiDevice(wires=1, client=stub)

    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(0)
        return qml.probs(wires=[0]), qml.expval(qml.PauliX(0))

    probs, expval_x = circuit()

    assert probs.shape == (2,)
    assert probs[0] == pytest.approx(0.5, abs=1e-9)
    assert probs[1] == pytest.approx(0.5, abs=1e-9)
    assert float(expval_x) == pytest.approx(1.0, abs=1e-9)
    assert len(stub.payloads) == 2
    assert all(payload["shots"] is None for payload in stub.payloads)
    assert all(payload["include_statevector"] is True for payload in stub.payloads)


def test_quantum_api_device_rejects_shot_vectors() -> None:
    stub = StubQuantumApiClient(
        {
            "detected_qasm_version": "2",
            "num_qubits": 1,
            "shots": 10,
            "counts": {"0": 10},
            "backend_mode": "qiskit",
            "statevector": None,
        }
    )

    QuantumApiDevice = _quantum_api_device_class()
    dev = QuantumApiDevice(wires=1, client=stub)

    @qml.set_shots((5, 5))
    @qml.qnode(dev)
    def circuit():
        return qml.expval(qml.PauliZ(0))

    with pytest.raises(Exception, match="Shot vectors are not supported"):
        circuit()
