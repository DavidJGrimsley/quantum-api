from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from quantum_api.config import get_settings
from quantum_api.main import app
from quantum_api.services.quantum_runtime import runtime
from quantum_api.supabase_auth import AuthenticatedUser

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)

QASM2_BELL = (
    'OPENQASM 2.0; include "qelib1.inc"; '
    "qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; "
    "measure q[0] -> c[0]; measure q[1] -> c[1];"
)


def _mock_user(monkeypatch, *, user_id: str, expected_token: str = "Bearer test-token") -> dict[str, str]:
    async def fake_verify(authorization_header: str | None) -> AuthenticatedUser:
        assert authorization_header == expected_token
        return AuthenticatedUser(
            user_id=user_id,
            email=f"{user_id}@example.test",
            claims={"sub": user_id, "aud": "authenticated"},
        )

    monkeypatch.setattr(app.state.jwt_verifier, "verify_authorization_header", fake_verify)
    return {"Authorization": expected_token}


def _create_profile(unauth_client, headers: dict[str, str], *, name: str = "IBM Open") -> dict[str, str]:
    response = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": name,
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
            "is_default": True,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _create_runtime_key(unauth_client, headers: dict[str, str]) -> str:
    response = unauth_client.post("/v1/keys", json={"name": "hardware"}, headers=headers)
    assert response.status_code == 200
    return response.json()["raw_key"]


@dataclass
class _FakeRemoteJob:
    status_value: str = "DONE"
    counts: dict[str, int] | None = None

    def status(self):
        return self.status_value

    def job_id(self):
        return "remote-job-123"

    def cancel(self):
        self.status_value = "CANCELLED"

    def result(self):
        counts = self.counts or {"00": 512, "11": 512}

        class _CountsRegister:
            def __init__(self, payload):
                self._payload = payload

            def get_counts(self):
                return self._payload

        class _Data:
            def __init__(self, payload):
                self.meas = _CountsRegister(payload)

        class _PubResult:
            def __init__(self, payload):
                self.data = _Data(payload)

        return [_PubResult(counts)]


class _FakeSampler:
    def __init__(self, mode=None):
        self.mode = mode

    def run(self, circuits, shots=1024):
        return _FakeRemoteJob(status_value="QUEUED")


@requires_qiskit
@pytest.mark.parametrize("initial_status", ["QUEUED", "DONE"])
def test_hardware_job_submit_status_result_and_cancel_flow(unauth_client, monkeypatch, initial_status):
    headers = _mock_user(monkeypatch, user_id=f"hardware-user-{initial_status}")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)
    monkeypatch.setattr(_FakeSampler, "run", lambda *args, **kwargs: _FakeRemoteJob(status_value=initial_status))

    remote_job = _FakeRemoteJob(status_value="DONE", counts={"00": 300, "11": 724})

    class _FakeService:
        def job(self, job_id):
            assert job_id == "remote-job-123"
            return remote_job

    monkeypatch.setattr("quantum_api.services.hardware_jobs.build_ibm_service", lambda credentials: _FakeService())

    submitted = unauth_client.post(
        "/v1/jobs/circuits",
        json={
            "provider": "ibm",
            "backend_name": "ibm_fake_backend",
            "circuit": {
                "num_qubits": 2,
                "operations": [
                    {"gate": "h", "target": 0},
                    {"gate": "cx", "control": 0, "target": 1},
                ],
            },
            "shots": 1024,
        },
        headers={"X-API-Key": raw_key},
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["job_id"]
    assert submitted.json()["status"] == ("queued" if initial_status == "QUEUED" else "succeeded")

    status = unauth_client.get(f"/v1/jobs/{job_id}", headers={"X-API-Key": raw_key})
    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"

    result = unauth_client.get(f"/v1/jobs/{job_id}/result", headers={"X-API-Key": raw_key})
    assert result.status_code == 200
    assert result.json()["result"]["counts"] == {"00": 300, "11": 724}

    cancelled = unauth_client.post(f"/v1/jobs/{job_id}/cancel", headers={"X-API-Key": raw_key})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "succeeded"


@requires_qiskit
@pytest.mark.parametrize("initial_status", ["QUEUED", "DONE"])
def test_hardware_qasm_job_submit_status_result_and_cancel_flow(unauth_client, monkeypatch, initial_status):
    headers = _mock_user(monkeypatch, user_id=f"hardware-qasm-user-{initial_status}")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)
    monkeypatch.setattr(_FakeSampler, "run", lambda *args, **kwargs: _FakeRemoteJob(status_value=initial_status))

    remote_job = _FakeRemoteJob(status_value="DONE", counts={"00": 256, "11": 768})

    class _FakeService:
        def job(self, job_id):
            assert job_id == "remote-job-123"
            return remote_job

    monkeypatch.setattr("quantum_api.services.hardware_jobs.build_ibm_service", lambda credentials: _FakeService())

    submitted = unauth_client.post(
        "/v1/jobs/qasm",
        json={
            "provider": "ibm",
            "backend_name": "ibm_fake_backend",
            "qasm": QASM2_BELL,
            "qasm_version": "auto",
            "shots": 1024,
        },
        headers={"X-API-Key": raw_key},
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["job_id"]
    assert submitted.json()["status"] == ("queued" if initial_status == "QUEUED" else "succeeded")

    status = unauth_client.get(f"/v1/jobs/{job_id}", headers={"X-API-Key": raw_key})
    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"

    result = unauth_client.get(f"/v1/jobs/{job_id}/result", headers={"X-API-Key": raw_key})
    assert result.status_code == 200
    assert result.json()["result"]["counts"] == {"00": 256, "11": 768}

    cancelled = unauth_client.post(f"/v1/jobs/{job_id}/cancel", headers={"X-API-Key": raw_key})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "succeeded"


@requires_qiskit
def test_hardware_job_result_not_ready(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="hardware-pending-user")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)

    remote_job = _FakeRemoteJob(status_value="RUNNING")

    class _FakeService:
        def job(self, job_id):
            return remote_job

    monkeypatch.setattr("quantum_api.services.hardware_jobs.build_ibm_service", lambda credentials: _FakeService())

    submitted = unauth_client.post(
        "/v1/jobs/circuits",
        json={
            "provider": "ibm",
            "backend_name": "ibm_fake_backend",
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
        },
        headers={"X-API-Key": raw_key},
    )
    assert submitted.status_code == 200

    result = unauth_client.get(
        f"/v1/jobs/{submitted.json()['job_id']}/result",
        headers={"X-API-Key": raw_key},
    )
    assert result.status_code == 409
    assert result.json()["error"] == "result_not_ready"


@requires_qiskit
def test_hardware_jobs_are_user_scoped(unauth_client, monkeypatch):
    owner_headers = _mock_user(monkeypatch, user_id="job-owner")
    _create_profile(unauth_client, headers=owner_headers)
    owner_key = _create_runtime_key(unauth_client, headers=owner_headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)
    monkeypatch.setattr(
        "quantum_api.services.hardware_jobs.build_ibm_service",
        lambda credentials: type("FakeService", (), {"job": lambda self, job_id: _FakeRemoteJob(status_value="DONE")})(),
    )

    submitted = unauth_client.post(
        "/v1/jobs/circuits",
        json={
            "provider": "ibm",
            "backend_name": "ibm_fake_backend",
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
        },
        headers={"X-API-Key": owner_key},
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["job_id"]

    intruder_headers = _mock_user(
        monkeypatch,
        user_id="job-intruder",
        expected_token="Bearer intruder-token",
    )
    _create_profile(unauth_client, headers=intruder_headers, name="Intruder IBM")
    intruder_key = _create_runtime_key(unauth_client, headers=intruder_headers)

    rejected = unauth_client.get(f"/v1/jobs/{job_id}", headers={"X-API-Key": intruder_key})
    assert rejected.status_code == 404


@requires_qiskit
def test_hardware_circuit_job_rejects_backend_qubit_capacity_mismatch(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="hardware-capacity-user")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    class _TinyBackend:
        def configuration(self):
            return SimpleNamespace(backend_name="ibm_tiny_backend", n_qubits=1, simulator=False)

    monkeypatch.setattr(
        "quantum_api.services.hardware_jobs.resolve_backend",
        lambda *args, **kwargs: ("ibm", _TinyBackend()),
    )

    submitted = unauth_client.post(
        "/v1/jobs/circuits",
        json={
            "provider": "ibm",
            "backend_name": "ibm_tiny_backend",
            "circuit": {
                "num_qubits": 2,
                "operations": [{"gate": "x", "target": 1}],
            },
            "shots": 256,
        },
        headers={"X-API-Key": raw_key},
    )
    assert submitted.status_code == 400
    payload = submitted.json()
    assert payload["error"] == "backend_qubit_capacity_exceeded"
    assert payload["details"]["backend_name"] == "ibm_tiny_backend"
    assert payload["details"]["provider"] == "ibm"
    assert payload["details"]["requested_qubits"] == 2
    assert payload["details"]["available_qubits"] == 1


@pytest.fixture
def random_hardware(unauth_client, monkeypatch, request):
    headers = _mock_user(monkeypatch, user_id=f"random-{request.node.name}")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)
    context = SimpleNamespace(
        headers={"X-API-Key": raw_key}, initial_status="QUEUED", bits=["1"],
        simulator=False, result_calls=0, submissions=[], records=[], resolved=[],
        remote=_FakeRemoteJob(status_value="DONE"), malformed=None,
    )

    def resolve(*args, **kwargs):
        context.resolved.append(kwargs["ibm_credentials"])
        return "ibm", SimpleNamespace(simulator=context.simulator, num_qubits=1)

    class Sampler:
        def __init__(self, mode):
            self.mode = mode

        def run(self, circuits, shots):
            context.submissions.append((circuits, shots))
            return _FakeRemoteJob(status_value=context.initial_status)

    def result():
        context.result_calls += 1
        if context.malformed == "exception":
            raise RuntimeError("sensitive-provider-error-must-not-be-returned")
        if context.malformed == "counts":
            return _FakeRemoteJob().result()
        if context.malformed == "empty":
            return []
        register = SimpleNamespace(get_bitstrings=lambda: context.bits)
        return [SimpleNamespace(data=SimpleNamespace(meas=register))]

    monkeypatch.setattr(context.remote, "result", result)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", resolve)
    monkeypatch.setattr(runtime, "transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr(runtime, "SamplerV2", Sampler)
    monkeypatch.setattr(
        "quantum_api.services.hardware_jobs.build_ibm_service",
        lambda credentials: SimpleNamespace(job=lambda job_id: context.remote),
    )
    original_create = app.state.execution_job_service.create_job

    async def create_job(**kwargs):
        record = await original_create(**kwargs)
        context.records.append(record)
        return record

    monkeypatch.setattr(app.state.execution_job_service, "create_job", create_job)

    def submit(**kwargs):
        return unauth_client.post(
            "/v1/jobs/random",
            json={"min": 0, "max": 1, "backend_name": "ibm_random_test", **kwargs},
            headers=context.headers,
        )

    context.submit = submit
    return context


@requires_qiskit
@pytest.mark.parametrize("initial_status", ["QUEUED", "DONE"])
@pytest.mark.parametrize("bit", ["0", "1"])
def test_random_hardware_lifecycle(unauth_client, random_hardware, initial_status, bit):
    context = random_hardware
    context.initial_status = initial_status
    context.bits = [bit]
    submitted = context.submit(ibm_profile="IBM Open")
    assert submitted.status_code == 200
    payload = submitted.json()
    assert set(payload) == {"job_id", "provider", "backend_name", "ibm_profile", "remote_job_id", "status", "created_at"}
    assert payload["ibm_profile"] == "IBM Open"
    record = context.records[0]
    assert record.request_payload["job_kind"] == "random"
    assert record.request_payload["shots"] == 1
    assert record.credential_token_ciphertext
    assert record.credential_token_ciphertext != context.resolved[0].token
    circuits, shots = context.submissions[0]
    assert shots == 1
    assert len(circuits) == 1
    circuit = circuits[0]
    assert circuit.num_qubits == 1
    assert circuit.num_clbits == 1
    assert [item.operation.name for item in circuit.data] == ["h", "barrier", "measure"]
    result_path = f"/v1/jobs/{payload['job_id']}/result"
    result = unauth_client.get(result_path, headers=context.headers)
    assert result.status_code == 200
    assert result.json() == {
        "job_id": payload["job_id"], "status": "succeeded",
        "result": {"value": int(bit), "source": "ibm-hardware"},
    }
    assert unauth_client.get(result_path, headers=context.headers).json() == result.json()
    assert context.result_calls == 1
    status = unauth_client.get(f"/v1/jobs/{payload['job_id']}", headers=context.headers)
    assert status.json()["status"] == "succeeded"
    assert status.json()["completed_at"] is not None


@requires_qiskit
@pytest.mark.parametrize("minimum,maximum,bits,expected", [
    (-1, 1, ["1", "1", "1", "0"] + ["0"] * 60, 1),
    (7, 7, ["1"], 7),
    (-2147483648, 2147483647, ["1"] * 32, 2147483647),
    (-2147483648, 2147483646, ["1"] * 32 + ["0"] * 992, -2147483648),
])
def test_random_hardware_ranges(unauth_client, random_hardware, minimum, maximum, bits, expected):
    random_hardware.bits = bits
    response = random_hardware.submit(min=minimum, max=maximum)
    assert response.status_code == 200
    assert random_hardware.submissions[0][1] == len(bits)
    result = unauth_client.get(f"/v1/jobs/{response.json()['job_id']}/result", headers=random_hardware.headers)
    assert result.status_code == 200
    assert result.json()["result"] == {"value": expected, "source": "ibm-hardware"}


@requires_qiskit
@pytest.mark.parametrize("simulator", [True, None])
def test_random_hardware_rejects_simulator_and_unknown_backend(random_hardware, simulator):
    random_hardware.simulator = simulator
    response = random_hardware.submit()
    assert response.status_code == 400
    assert response.json()["error"] == "hardware_backend_required"
    assert random_hardware.submissions == []
    assert random_hardware.records == []


@requires_qiskit
@pytest.mark.parametrize("malformed,bits,maximum,reason", [
    ("counts", ["0"], 1, "malformed_provider_result"),
    ("empty", ["0"], 1, "malformed_provider_result"),
    (None, ["00"], 1, "malformed_provider_result"),
    (None, ["0", "1"], 1, "malformed_provider_result"),
    (None, ["1"] * 64, 2, "rejection_exhausted"),
    ("exception", ["0"], 1, "provider_result_unavailable"),
])
def test_random_hardware_persists_failed_results(unauth_client, random_hardware, malformed, bits, maximum, reason):
    random_hardware.malformed = malformed
    random_hardware.bits = bits
    submitted = random_hardware.submit(max=maximum)
    job_id = submitted.json()["job_id"]
    response = unauth_client.get(f"/v1/jobs/{job_id}", headers=random_hardware.headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error"]["error"] == "provider_job_failed"
    assert payload["error"]["details"]["reason"] == reason
    assert payload["completed_at"] is not None
    assert "sensitive-provider-error" not in response.text
    again = unauth_client.get(f"/v1/jobs/{job_id}", headers=random_hardware.headers)
    assert again.json() == payload
    result = unauth_client.get(f"/v1/jobs/{job_id}/result", headers=random_hardware.headers)
    assert result.status_code == 409
    assert result.json()["details"]["status"] == "failed"
    assert random_hardware.result_calls == 1


@requires_qiskit
def test_random_hardware_pending_cancel_and_owner_isolation(unauth_client, monkeypatch, random_hardware):
    random_hardware.remote.status_value = "RUNNING"
    submitted = random_hardware.submit()
    job_path = f"/v1/jobs/{submitted.json()['job_id']}"
    pending = unauth_client.get(f"{job_path}/result", headers=random_hardware.headers)
    assert pending.status_code == 409
    assert pending.json()["details"]["status"] == "running"
    other = _mock_user(monkeypatch, user_id="random-intruder", expected_token="Bearer other")
    other_key = _create_runtime_key(unauth_client, headers=other)
    for method, path in [("get", job_path), ("get", f"{job_path}/result"), ("post", f"{job_path}/cancel")]:
        denied = getattr(unauth_client, method)(path, headers={"X-API-Key": other_key})
        assert denied.status_code == 404
    cancelled = unauth_client.post(f"{job_path}/cancel", headers=random_hardware.headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert random_hardware.result_calls == 0


@requires_qiskit
def test_random_hardware_missing_dependency(random_hardware, monkeypatch):
    monkeypatch.setattr(runtime, "SamplerV2", None)
    response = random_hardware.submit()
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"
    assert random_hardware.submissions == []


def test_random_hardware_requires_provider_credentials(client):
    response = client.post("/v1/jobs/random", json={"min": 0, "max": 1, "backend_name": "ibm_test"})
    assert response.status_code == 503
    assert response.json()["error"] == "provider_credentials_missing"


def test_random_hardware_uses_server_environment_credentials(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="random-environment-credentials")
    raw_key = _create_runtime_key(unauth_client, headers=headers)
    settings = get_settings()
    monkeypatch.setattr(settings, "ibm_token", "fake-environment-token")
    monkeypatch.setattr(settings, "ibm_instance", "fake-environment-instance")
    monkeypatch.setattr(settings, "ibm_channel", "ibm_quantum_platform")
    observed = {}

    async def submit_random_job(**kwargs):
        observed["credentials"] = kwargs["ibm_credentials"]
        return SimpleNamespace(
            job_id="environment-random-job",
            provider="ibm",
            backend_name=kwargs["request_data"].backend_name,
            ibm_profile_name=None,
            remote_job_id="environment-remote-job",
            status="queued",
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(app.state.hardware_job_service, "submit_random_job", submit_random_job)
    response = unauth_client.post(
        "/v1/jobs/random",
        json={"min": 0, "max": 1, "backend_name": "ibm_environment_test"},
        headers={"X-API-Key": raw_key},
    )

    assert response.status_code == 200
    assert response.json()["ibm_profile"] is None
    credentials = observed["credentials"]
    assert credentials.source == "server_env"
    assert credentials.token_ciphertext
    assert credentials.token_ciphertext != credentials.token
    assert "fake-environment-token" not in response.text


@requires_qiskit
def test_hardware_qasm_job_rejects_backend_qubit_capacity_mismatch(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="hardware-capacity-qasm-user")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    class _TinyBackend:
        def configuration(self):
            return SimpleNamespace(backend_name="ibm_tiny_backend", n_qubits=1, simulator=False)

    monkeypatch.setattr(
        "quantum_api.services.hardware_jobs.resolve_backend",
        lambda *args, **kwargs: ("ibm", _TinyBackend()),
    )

    submitted = unauth_client.post(
        "/v1/jobs/qasm",
        json={
            "provider": "ibm",
            "backend_name": "ibm_tiny_backend",
            "qasm": QASM2_BELL,
            "qasm_version": "auto",
            "shots": 256,
        },
        headers={"X-API-Key": raw_key},
    )
    assert submitted.status_code == 400
    payload = submitted.json()
    assert payload["error"] == "backend_qubit_capacity_exceeded"
    assert payload["details"]["backend_name"] == "ibm_tiny_backend"
    assert payload["details"]["provider"] == "ibm"
    assert payload["details"]["requested_qubits"] == 2
    assert payload["details"]["available_qubits"] == 1
