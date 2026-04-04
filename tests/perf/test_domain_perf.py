from __future__ import annotations

import time

import pytest

from quantum_api.models.api import (
    AmplitudeEstimationRequest,
    FinancePortfolioDiversificationRequest,
    GroverSearchRequest,
    OptimizationKnapsackRequest,
    OptimizationMaxcutRequest,
    OptimizationQaoaRequest,
    OptimizationTspRequest,
    OptimizationVqeRequest,
    PhaseEstimationRequest,
    QuantumVolumeRequest,
    RandomizedBenchmarkingRequest,
    StateTomographyRequest,
    T1ExperimentRequest,
    T2RamseyExperimentRequest,
    TimeEvolutionRequest,
)
from quantum_api.services.algorithms.amplitude_estimation import run_amplitude_estimation
from quantum_api.services.algorithms.grover_search import run_grover_search
from quantum_api.services.algorithms.phase_estimation import run_phase_estimation
from quantum_api.services.algorithms.time_evolution import run_time_evolution
from quantum_api.services.experiments.quantum_volume import run_quantum_volume
from quantum_api.services.experiments.randomized_benchmarking import run_randomized_benchmarking
from quantum_api.services.experiments.state_tomography import run_state_tomography
from quantum_api.services.experiments.t1 import run_t1_experiment
from quantum_api.services.experiments.t2ramsey import run_t2ramsey_experiment
from quantum_api.services.finance.portfolio_diversification import solve_portfolio_diversification
from quantum_api.services.optimization.knapsack import solve_knapsack
from quantum_api.services.optimization.maxcut import solve_maxcut
from quantum_api.services.optimization.qaoa import solve_qaoa
from quantum_api.services.optimization.tsp import solve_tsp
from quantum_api.services.optimization.vqe import solve_vqe
from quantum_api.services.quantum_runtime import runtime


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_algorithms_available, reason="Algorithm dependencies unavailable")
def test_grover_perf_budget():
    started = time.perf_counter()
    run_grover_search(
        GroverSearchRequest.model_validate(
            {
                "marked_bitstrings": ["11"],
                "iterations": [1],
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_algorithms_available, reason="Algorithm dependencies unavailable")
def test_amplitude_estimation_perf_budget():
    started = time.perf_counter()
    run_amplitude_estimation(
        AmplitudeEstimationRequest.model_validate(
            {
                "variant": "ae",
                "state_preparation": {
                    "num_qubits": 1,
                    "operations": [{"gate": "ry", "target": 0, "theta": 1.2}],
                },
                "objective_qubits": [0],
                "num_eval_qubits": 2,
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_algorithms_available, reason="Algorithm dependencies unavailable")
def test_phase_estimation_perf_budget():
    started = time.perf_counter()
    run_phase_estimation(
        PhaseEstimationRequest.model_validate(
            {
                "variant": "standard",
                "unitary": {
                    "num_qubits": 1,
                    "operations": [{"gate": "z", "target": 0}],
                },
                "state_preparation": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "num_evaluation_qubits": 3,
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_algorithms_available, reason="Algorithm dependencies unavailable")
def test_time_evolution_perf_budget():
    started = time.perf_counter()
    run_time_evolution(
        TimeEvolutionRequest.model_validate(
            {
                "variant": "trotter_qrte",
                "hamiltonian": [{"pauli": "Z", "coefficient": 1.0}],
                "time": 0.5,
                "initial_state": {
                    "num_qubits": 1,
                    "operations": [{"gate": "h", "target": 0}],
                },
                "num_timesteps": 2,
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Optimization dependencies unavailable",
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
@pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Optimization dependencies unavailable",
)
def test_maxcut_perf_budget():
    started = time.perf_counter()
    solve_maxcut(
        OptimizationMaxcutRequest.model_validate(
            {
                "num_nodes": 3,
                "edges": [
                    {"source": 0, "target": 1, "weight": 1.5},
                    {"source": 1, "target": 2, "weight": 2.0},
                    {"source": 0, "target": 2, "weight": 0.5},
                ],
                "solver": "exact",
                "reps": 1,
                "optimizer": {"name": "cobyla", "maxiter": 5},
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Optimization dependencies unavailable",
)
def test_knapsack_perf_budget():
    started = time.perf_counter()
    solve_knapsack(
        OptimizationKnapsackRequest.model_validate(
            {
                "item_values": [3, 4, 5],
                "item_weights": [2, 3, 4],
                "capacity": 5,
                "solver": "exact",
                "reps": 1,
                "optimizer": {"name": "cobyla", "maxiter": 5},
                "shots": 128,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(
    not (runtime.qiskit_algorithms_available and runtime.qiskit_optimization_available),
    reason="Optimization dependencies unavailable",
)
def test_tsp_perf_budget():
    started = time.perf_counter()
    solve_tsp(
        OptimizationTspRequest.model_validate(
            {
                "distance_matrix": [
                    [0.0, 10.0, 15.0, 20.0],
                    [10.0, 0.0, 35.0, 25.0],
                    [15.0, 35.0, 0.0, 30.0],
                    [20.0, 25.0, 30.0, 0.0],
                ],
                "solver": "exact",
                "reps": 1,
                "optimizer": {"name": "cobyla", "maxiter": 5},
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
@pytest.mark.skipif(
    not (runtime.qiskit_finance_available and runtime.qiskit_optimization_available and runtime.qiskit_algorithms_available),
    reason="Finance dependencies unavailable",
)
def test_portfolio_diversification_perf_budget():
    started = time.perf_counter()
    solve_portfolio_diversification(
        FinancePortfolioDiversificationRequest.model_validate(
            {
                "similarity_matrix": [
                    [1.0, 0.2, 0.3],
                    [0.2, 1.0, 0.4],
                    [0.3, 0.4, 1.0],
                ],
                "num_clusters": 2,
                "asset_labels": ["ALPHA", "BETA", "GAMMA"],
                "solver": "exact",
                "optimizer": {"name": "cobyla", "maxiter": 5},
                "reps": 1,
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


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_experiments_available, reason="Experiment dependencies unavailable")
def test_quantum_volume_perf_budget():
    started = time.perf_counter()
    run_quantum_volume(
        QuantumVolumeRequest.model_validate(
            {
                "qubits": [0, 1],
                "trials": 3,
                "shots": 64,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_experiments_available, reason="Experiment dependencies unavailable")
def test_t1_perf_budget():
    started = time.perf_counter()
    run_t1_experiment(
        T1ExperimentRequest.model_validate(
            {
                "qubits": [0],
                "delays": [0.000001, 0.000002, 0.000003, 0.000004],
                "shots": 64,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20


@pytest.mark.perf
@pytest.mark.skipif(not runtime.qiskit_experiments_available, reason="Experiment dependencies unavailable")
def test_t2ramsey_perf_budget():
    started = time.perf_counter()
    run_t2ramsey_experiment(
        T2RamseyExperimentRequest.model_validate(
            {
                "qubits": [0],
                "delays": [0.000001, 0.000002, 0.000003, 0.000004, 0.000005],
                "osc_freq": 100000.0,
                "shots": 64,
                "seed": 7,
            }
        )
    )
    assert time.perf_counter() - started < 20
