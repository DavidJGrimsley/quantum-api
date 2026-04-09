from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

from quantum_api.ibm_credentials import ResolvedIbmCredentials, mask_ibm_token
from quantum_api.models.api import CircuitRunRequest, QasmRunRequest
from quantum_api.models.machine_learning import QsvrRegressorRequest
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.ibm_provider import build_ibm_service, clear_ibm_provider_cache
from quantum_api.services.machine_learning.qsvr_regressor import run_qsvr_regressor
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.transpilation import run_qasm

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)

requires_machine_learning = pytest.mark.skipif(
    not runtime.qiskit_machine_learning_available or not runtime.qiskit_algorithms_available,
    reason="machine-learning dependencies unavailable",
)

_QASM2_BELL = (
    'OPENQASM 2.0; include "qelib1.inc"; '
    "qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; "
    "measure q[0] -> c[0]; measure q[1] -> c[1];"
)


@requires_qiskit
def test_concurrent_circuit_runs_are_seed_stable():
    def _request() -> CircuitRunRequest:
        return CircuitRunRequest(
            num_qubits=2,
            operations=[
                {"gate": "h", "target": 0},
                {"gate": "cx", "control": 0, "target": 1},
            ],
            shots=256,
            seed=19,
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        payloads = list(executor.map(lambda _: run_circuit(_request()), range(18)))

    first_counts = payloads[0]["counts"]
    assert all(payload["counts"] == first_counts for payload in payloads)


@requires_qiskit
def test_concurrent_qasm_runs_are_seed_stable():
    def _request() -> QasmRunRequest:
        return QasmRunRequest(
            qasm=_QASM2_BELL,
            qasm_version="auto",
            shots=256,
            include_statevector=False,
            seed=23,
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        payloads = list(executor.map(lambda _: run_qasm(_request()), range(18)))

    first_counts = payloads[0]["counts"]
    assert all(payload["counts"] == first_counts for payload in payloads)


@requires_machine_learning
def test_concurrent_qsvr_runs_are_seed_stable():
    def _request() -> QsvrRegressorRequest:
        return QsvrRegressorRequest.model_validate(
            {
                "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
                "training_targets": [0.0, 1.0, 1.0, 0.0],
                "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
                "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
                "seed": 7,
            }
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        payloads = list(executor.map(lambda _: run_qsvr_regressor(_request()), range(8)))

    first = payloads[0]
    assert all(payload["predictions"] == first["predictions"] for payload in payloads)
    assert all(payload["training_score"] == first["training_score"] for payload in payloads)



def test_concurrent_ibm_service_cache_returns_consistent_instance(monkeypatch):
    init_calls = 0
    init_lock = Lock()

    class _FakeRuntimeService:
        def __init__(self, *, token: str, instance: str, channel: str) -> None:
            nonlocal init_calls
            # Simulate a slow provider client init so multiple threads race through cache lookup.
            time.sleep(0.01)
            with init_lock:
                init_calls += 1
            self.token = token
            self.instance = instance
            self.channel = channel

    clear_ibm_provider_cache()
    monkeypatch.setattr(runtime, "ibm_runtime_available", True)
    monkeypatch.setattr(runtime, "QiskitRuntimeService", _FakeRuntimeService)

    credentials = ResolvedIbmCredentials(
        owner_user_id="concurrency-user",
        profile_id="profile-1",
        profile_name="default",
        instance="instance-a",
        channel="ibm_quantum_platform",
        masked_token=mask_ibm_token("tok_cache_race"),
        token="tok_cache_race",
        token_ciphertext="ciphertext",
        source="profile",
    )

    with ThreadPoolExecutor(max_workers=10) as executor:
        service_ids = list(executor.map(lambda _: id(build_ibm_service(credentials)), range(30)))

    assert len(set(service_ids)) == 1
    assert init_calls >= 1
