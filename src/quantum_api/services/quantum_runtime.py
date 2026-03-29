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
    Aer: Any | None
    qasm2: Any | None
    qasm3: Any | None
    QiskitRuntimeService: Any | None
    ibm_runtime_available: bool
    ibm_runtime_import_error: str | None

    @property
    def mode(self) -> str:
        return "qiskit" if self.qiskit_available else "classical-fallback"


def build_runtime() -> QuantumRuntime:
    try:
        from qiskit import QuantumCircuit, qasm2, qasm3, transpile
        from qiskit.quantum_info import Statevector
        from qiskit_aer import Aer, AerSimulator

        qiskit_available = True
        import_error = None
    except Exception as exc:  # pragma: no cover - exercised in environments without qiskit
        qiskit_available = False
        import_error = str(exc)
        QuantumCircuit = None
        Statevector = None
        transpile = None
        AerSimulator = None
        Aer = None
        qasm2 = None
        qasm3 = None

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        ibm_runtime_available = True
        ibm_runtime_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        QiskitRuntimeService = None
        ibm_runtime_available = False
        ibm_runtime_import_error = str(exc)

    return QuantumRuntime(
        qiskit_available=qiskit_available,
        import_error=import_error,
        QuantumCircuit=QuantumCircuit,
        Statevector=Statevector,
        transpile=transpile,
        AerSimulator=AerSimulator,
        Aer=Aer,
        qasm2=qasm2,
        qasm3=qasm3,
        QiskitRuntimeService=QiskitRuntimeService,
        ibm_runtime_available=ibm_runtime_available,
        ibm_runtime_import_error=ibm_runtime_import_error,
    )


runtime = build_runtime()
