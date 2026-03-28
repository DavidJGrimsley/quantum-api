"""Runtime import detection for qiskit support."""

from dataclasses import dataclass
from typing import Any


@dataclass
class QuantumRuntime:
    qiskit_available: bool
    import_error: str | None
    QuantumCircuit: Any | None
    Statevector: Any | None
    transpile: Any | None
    AerSimulator: Any | None

    @property
    def mode(self) -> str:
        return "qiskit" if self.qiskit_available else "classical-fallback"


def build_runtime() -> QuantumRuntime:
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit.quantum_info import Statevector
        from qiskit_aer import AerSimulator

        return QuantumRuntime(
            qiskit_available=True,
            import_error=None,
            QuantumCircuit=QuantumCircuit,
            Statevector=Statevector,
            transpile=transpile,
            AerSimulator=AerSimulator,
        )
    except Exception as exc:  # pragma: no cover - exercised in environments without qiskit
        return QuantumRuntime(
            qiskit_available=False,
            import_error=str(exc),
            QuantumCircuit=None,
            Statevector=None,
            transpile=None,
            AerSimulator=None,
        )


runtime = build_runtime()
