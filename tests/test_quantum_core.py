from __future__ import annotations

from types import SimpleNamespace

import pytest

from quantum_api.services.quantum_core import QuantumCircuitManager


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
