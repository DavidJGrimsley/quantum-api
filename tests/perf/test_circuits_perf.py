import math
import os
import time

import pytest

from quantum_api.models.api import CircuitRunRequest
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.quantum_runtime import runtime

RUN_PERF_BENCHMARKS = os.getenv("RUN_PERF_BENCHMARKS", "false").lower() == "true"

pytestmark = [
    pytest.mark.perf,
    pytest.mark.skipif(not RUN_PERF_BENCHMARKS, reason="Set RUN_PERF_BENCHMARKS=true to run perf tests."),
    pytest.mark.skipif(not runtime.qiskit_available, reason="qiskit runtime unavailable"),
]


def _run_and_measure(request: CircuitRunRequest) -> float:
    started = time.perf_counter()
    payload = run_circuit(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert sum(payload["counts"].values()) == request.shots
    return elapsed_ms


def test_perf_bell_circuit():
    elapsed_ms = _run_and_measure(
        CircuitRunRequest(
            num_qubits=2,
            operations=[
                {"gate": "h", "target": 0},
                {"gate": "cx", "control": 0, "target": 1},
            ],
            shots=1024,
            seed=11,
        )
    )
    print(f"bell_circuit_elapsed_ms={elapsed_ms:.3f}")
    assert elapsed_ms > 0


def test_perf_ghz_circuit():
    elapsed_ms = _run_and_measure(
        CircuitRunRequest(
            num_qubits=3,
            operations=[
                {"gate": "h", "target": 0},
                {"gate": "cx", "control": 0, "target": 1},
                {"gate": "cx", "control": 1, "target": 2},
            ],
            shots=1024,
            seed=11,
        )
    )
    print(f"ghz_circuit_elapsed_ms={elapsed_ms:.3f}")
    assert elapsed_ms > 0


def test_perf_rotation_circuit():
    elapsed_ms = _run_and_measure(
        CircuitRunRequest(
            num_qubits=1,
            operations=[{"gate": "ry", "target": 0, "theta": math.pi / 2}],
            shots=1024,
            seed=11,
        )
    )
    print(f"rotation_circuit_elapsed_ms={elapsed_ms:.3f}")
    assert elapsed_ms > 0
