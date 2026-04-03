from __future__ import annotations

import time

import pytest

from quantum_api.models.api import (
    OptimizationQaoaRequest,
    OptimizationVqeRequest,
    RandomizedBenchmarkingRequest,
    StateTomographyRequest,
)
from quantum_api.services.phase5_experiments import (
    run_randomized_benchmarking,
    run_state_tomography,
)
from quantum_api.services.phase5_optimization import solve_qaoa, solve_vqe
from quantum_api.services.quantum_runtime import runtime


@pytest.mark.perf
@pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Phase 5 optimization dependencies unavailable",
)
def test_qaoa_perf_budget():
    started = time.perf_counter()
    solve_qaoa(
        OptimizationQaoaRequest.model_validate(
            {
                "problem": {
                    "num_variables": 2,
                    "linear": [1.0, -2.0],
                    "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
                },
                "optimizer": {"name": "cobyla", "maxiter": 5},
                "reps": 1,
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_algorithms_available, reason="VQE dependencies unavailable")
def test_vqe_perf_budget():
    started = time.perf_counter()
    solve_vqe(
        OptimizationVqeRequest.model_validate(
            {
                "pauli_sum": [
                    {"pauli": "ZI", "coefficient": 1.0},
                    {"pauli": "IZ", "coefficient": -0.5},
                    {"pauli": "XX", "coefficient": 0.2},
                ],
                "optimizer": {"name": "cobyla", "maxiter": 5},
                "ansatz": {"type": "real_amplitudes", "reps": 1},
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_experiments_available, reason="Experiment dependencies unavailable")
def test_tomography_perf_budget():
    started = time.perf_counter()
    run_state_tomography(
        StateTomographyRequest.model_validate(
            {
                "circuit": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_experiments_available, reason="Experiment dependencies unavailable")
def test_randomized_benchmarking_perf_budget():
    started = time.perf_counter()
    run_randomized_benchmarking(
        RandomizedBenchmarkingRequest.model_validate(
            {
                "qubits": [0],
                "sequence_lengths": [1, 2, 4],
                "num_samples": 2,
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20
