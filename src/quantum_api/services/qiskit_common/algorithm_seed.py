from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime

_ALGORITHM_GLOBALS_LOCK = RLock()


@contextmanager
def scoped_algorithm_seed(seed: int | None) -> Iterator[None]:
    if seed is None:
        yield
        return

    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )
    from qiskit_algorithms.utils import algorithm_globals

    with _ALGORITHM_GLOBALS_LOCK:
        previous_seed = getattr(algorithm_globals, "random_seed", None)
        algorithm_globals.random_seed = seed
        try:
            yield
        finally:
            algorithm_globals.random_seed = previous_seed