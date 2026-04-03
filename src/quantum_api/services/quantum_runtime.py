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
    SamplerV2: Any | None
    ibm_runtime_available: bool
    ibm_runtime_import_error: str | None
    qiskit_algorithms_available: bool
    qiskit_algorithms_import_error: str | None
    qiskit_optimization_available: bool
    qiskit_optimization_import_error: str | None
    qiskit_experiments_available: bool
    qiskit_experiments_import_error: str | None
    qiskit_finance_available: bool
    qiskit_finance_import_error: str | None
    qiskit_machine_learning_available: bool
    qiskit_machine_learning_import_error: str | None
    qiskit_nature_available: bool
    qiskit_nature_import_error: str | None
    pyscf_available: bool
    pyscf_import_error: str | None

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
        from qiskit_ibm_runtime import (  # pyright: ignore[reportMissingImports]
            QiskitRuntimeService,
            SamplerV2,
        )

        ibm_runtime_available = True
        ibm_runtime_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        QiskitRuntimeService = None
        SamplerV2 = None
        ibm_runtime_available = False
        ibm_runtime_import_error = str(exc)

    try:
        import qiskit_algorithms  # noqa: F401

        qiskit_algorithms_available = True
        qiskit_algorithms_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_algorithms_available = False
        qiskit_algorithms_import_error = str(exc)

    try:
        import qiskit_optimization  # noqa: F401

        qiskit_optimization_available = True
        qiskit_optimization_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_optimization_available = False
        qiskit_optimization_import_error = str(exc)

    try:
        import qiskit_experiments  # noqa: F401

        qiskit_experiments_available = True
        qiskit_experiments_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_experiments_available = False
        qiskit_experiments_import_error = str(exc)

    try:
        import qiskit_finance  # noqa: F401

        qiskit_finance_available = True
        qiskit_finance_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_finance_available = False
        qiskit_finance_import_error = str(exc)

    try:
        import qiskit_machine_learning  # noqa: F401

        qiskit_machine_learning_available = True
        qiskit_machine_learning_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_machine_learning_available = False
        qiskit_machine_learning_import_error = str(exc)

    try:
        from qiskit_nature.second_q.drivers import PySCFDriver  # noqa: F401
        from qiskit_nature.second_q.mappers import JordanWignerMapper  # noqa: F401

        qiskit_nature_available = True
        qiskit_nature_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        qiskit_nature_available = False
        qiskit_nature_import_error = str(exc)

    try:
        import pyscf  # noqa: F401

        pyscf_available = True
        pyscf_import_error = None
    except Exception as exc:  # pragma: no cover - optional dependency
        pyscf_available = False
        pyscf_import_error = str(exc)

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
        SamplerV2=SamplerV2,
        ibm_runtime_available=ibm_runtime_available,
        ibm_runtime_import_error=ibm_runtime_import_error,
        qiskit_algorithms_available=qiskit_algorithms_available,
        qiskit_algorithms_import_error=qiskit_algorithms_import_error,
        qiskit_optimization_available=qiskit_optimization_available,
        qiskit_optimization_import_error=qiskit_optimization_import_error,
        qiskit_experiments_available=qiskit_experiments_available,
        qiskit_experiments_import_error=qiskit_experiments_import_error,
        qiskit_finance_available=qiskit_finance_available,
        qiskit_finance_import_error=qiskit_finance_import_error,
        qiskit_machine_learning_available=qiskit_machine_learning_available,
        qiskit_machine_learning_import_error=qiskit_machine_learning_import_error,
        qiskit_nature_available=qiskit_nature_available,
        qiskit_nature_import_error=qiskit_nature_import_error,
        pyscf_available=pyscf_available,
        pyscf_import_error=pyscf_import_error,
    )


runtime = build_runtime()
