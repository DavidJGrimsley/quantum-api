from __future__ import annotations

import random
from types import SimpleNamespace

import pytest

from quantum_api.services.quantum_core import QuantumCircuitManager, Qubit
from quantum_api.services.quantum_runtime import runtime


@pytest.mark.skipif(not runtime.qiskit_available, reason="Qiskit unavailable")
def test_qubit_uses_statevector_measure_and_syncs_collapse(monkeypatch):
    calls = []

    def measure(state):
        calls.append(state)
        return "1", runtime.Statevector([0, 1])

    monkeypatch.setattr(runtime.Statevector, "measure", measure)
    qubit = Qubit()
    qubit.hadamard()
    assert qubit.measure() == 1
    assert len(calls) == 1
    assert qubit.probabilities() == (0.0, 1.0)
    assert qubit.get_superposition_strength() == 0.0


@pytest.mark.parametrize("qiskit_available", [True, False])
@pytest.mark.parametrize("seed,expected", [(0, 1), (1, 0)])
def test_qubit_injected_rng_remains_deterministic(monkeypatch, qiskit_available, seed, expected):
    monkeypatch.setattr(runtime, "qiskit_available", qiskit_available)
    if runtime.Statevector is not None:
        def unexpected_measure(state):
            pytest.fail("Injected RNG must bypass Statevector.measure")

        monkeypatch.setattr(runtime.Statevector, "measure", unexpected_measure)
    qubit = Qubit()
    qubit.hadamard()
    assert qubit.measure(random.Random(seed)) == expected
    assert qubit.probabilities()[expected] == 1.0
    qubit.hadamard()
    assert qubit.probabilities() == pytest.approx((0.5, 0.5))


def test_quantum_circuit_manager_respects_configured_max_qubits(monkeypatch):
    monkeypatch.setattr(
        "quantum_api.services.quantum_core.get_settings",
        lambda: SimpleNamespace(max_circuit_qubits=12),
    )

    manager = QuantumCircuitManager(12)

    assert manager.num_qubits == 12


def test_quantum_circuit_manager_rejects_qubits_above_configured_max(monkeypatch):
    monkeypatch.setattr(
        "quantum_api.services.quantum_core.get_settings",
        lambda: SimpleNamespace(max_circuit_qubits=4),
    )

    with pytest.raises(ValueError, match="num_qubits must be between 1 and 4"):
        QuantumCircuitManager(5)
