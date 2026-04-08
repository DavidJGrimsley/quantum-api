from __future__ import annotations

from dataclasses import dataclass

import pytest

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
def test_hardware_job_submit_status_result_and_cancel_flow(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="hardware-user")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)

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
    assert submitted.json()["status"] == "queued"

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
def test_hardware_qasm_job_submit_status_result_and_cancel_flow(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="hardware-qasm-user")
    _create_profile(unauth_client, headers=headers)
    raw_key = _create_runtime_key(unauth_client, headers=headers)

    monkeypatch.setattr("quantum_api.services.hardware_jobs.resolve_backend", lambda *args, **kwargs: ("ibm", object()))
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.transpile", lambda circuit, backend: circuit)
    monkeypatch.setattr("quantum_api.services.hardware_jobs.runtime.SamplerV2", _FakeSampler)

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
    assert submitted.json()["status"] == "queued"

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
