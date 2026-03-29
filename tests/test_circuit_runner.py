import math

import pytest

from quantum_api.models.api import CircuitRunRequest
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.quantum_runtime import runtime

pytestmark = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)


def _to_complex_statevector(raw_statevector: list[dict[str, float]]) -> list[complex]:
    return [complex(item["real"], item["imag"]) for item in raw_statevector]


def test_run_circuit_deterministic_with_seed():
    request = CircuitRunRequest(
        num_qubits=2,
        operations=[
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
        ],
        shots=512,
        seed=17,
    )

    first = run_circuit(request)
    second = run_circuit(request)

    assert first["counts"] == second["counts"]


def test_run_circuit_counts_integrity():
    request = CircuitRunRequest(
        num_qubits=3,
        operations=[
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
            {"gate": "cx", "control": 1, "target": 2},
        ],
        shots=777,
        seed=3,
    )

    payload = run_circuit(request)
    counts = payload["counts"]

    assert sum(counts.values()) == request.shots
    assert all(len(bitstring) == request.num_qubits for bitstring in counts)


def test_run_circuit_bell_statevector_matches_expected():
    request = CircuitRunRequest(
        num_qubits=2,
        operations=[
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
        ],
        shots=16,
        include_statevector=True,
    )

    payload = run_circuit(request)
    statevector = _to_complex_statevector(payload["statevector"])

    expected = [1 / math.sqrt(2), 0, 0, 1 / math.sqrt(2)]
    assert len(statevector) == len(expected)
    for actual, target in zip(statevector, expected, strict=True):
        assert actual.real == pytest.approx(float(target), abs=1e-9)
        assert actual.imag == pytest.approx(0.0, abs=1e-9)


def test_run_circuit_ghz_statevector_matches_expected():
    request = CircuitRunRequest(
        num_qubits=3,
        operations=[
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
            {"gate": "cx", "control": 1, "target": 2},
        ],
        shots=16,
        include_statevector=True,
    )

    payload = run_circuit(request)
    statevector = _to_complex_statevector(payload["statevector"])

    assert len(statevector) == 8
    assert statevector[0].real == pytest.approx(1 / math.sqrt(2), abs=1e-9)
    assert statevector[7].real == pytest.approx(1 / math.sqrt(2), abs=1e-9)
    for index in range(1, 7):
        assert abs(statevector[index]) == pytest.approx(0.0, abs=1e-9)


def test_run_circuit_rotation_statevector_matches_expected():
    theta = math.pi / 3
    request = CircuitRunRequest(
        num_qubits=1,
        operations=[{"gate": "ry", "target": 0, "theta": theta}],
        shots=16,
        include_statevector=True,
    )

    payload = run_circuit(request)
    statevector = _to_complex_statevector(payload["statevector"])

    assert len(statevector) == 2
    assert statevector[0].real == pytest.approx(math.cos(theta / 2), abs=1e-9)
    assert statevector[1].real == pytest.approx(math.sin(theta / 2), abs=1e-9)
    assert statevector[0].imag == pytest.approx(0.0, abs=1e-9)
    assert statevector[1].imag == pytest.approx(0.0, abs=1e-9)
