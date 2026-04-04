from __future__ import annotations

from typing import Any

from quantum_api.models.machine_learning import FeatureMapConfig
from quantum_api.models.qiskit_common import AnsatzConfig
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def build_feature_map(num_features: int, config: FeatureMapConfig) -> Any:
    from qiskit.circuit.library import zz_feature_map

    return zz_feature_map(
        num_features,
        reps=config.reps,
        entanglement=config.entanglement,
    )


def build_ansatz(num_qubits: int, config: AnsatzConfig) -> Any:
    from qiskit.circuit.library import real_amplitudes

    return real_amplitudes(
        num_qubits,
        reps=config.reps,
        entanglement=config.entanglement,
    )


def python_scalar(value: Any) -> Any:
    return value.item() if hasattr(value, "item") else value


def python_list(values: Any) -> list[Any]:
    return [python_scalar(value) for value in values]


def set_algorithm_seed(seed: int | None) -> None:
    if seed is None:
        return

    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )
    from qiskit_algorithms.utils import algorithm_globals

    algorithm_globals.random_seed = seed
