from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

SDK_PYTHON_PATH = Path(__file__).resolve().parents[1] / "sdk" / "python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.append(str(SDK_PYTHON_PATH))


def test_python_sdk_injects_api_key_header() -> None:
    from quantum_api_sdk import QuantumApiClient

    captured_header: dict[str, str | None] = {"api_key": None}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_header["api_key"] = request.headers.get("X-API-Key")
        return httpx.Response(
            status_code=200,
            json={
                "status": "healthy",
                "service": "Quantum API",
                "version": "0.1.0",
                "qiskit_available": True,
                "runtime_mode": "qiskit",
            },
        )

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test/v1",
        api_key="sdk-secret",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        client.echo_types()
    assert captured_header["api_key"] == "sdk-secret"


def test_python_sdk_normalizes_base_url_and_uses_public_health_route() -> None:
    from quantum_api_sdk import QuantumApiClient

    captured_url: dict[str, str | None] = {"url": None}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_url["url"] = str(request.url)
        return httpx.Response(
            status_code=200,
            json={
                "status": "healthy",
                "service": "Quantum API",
                "version": "0.1.0",
                "qiskit_available": True,
                "runtime_mode": "qiskit",
            },
        )

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test/public-facing/api/quantum",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        client.health()

    assert captured_url["url"] == "http://example.test/public-facing/api/quantum/v1/health"


def test_python_sdk_uses_bearer_token_for_key_routes() -> None:
    from quantum_api_sdk import QuantumApiClient

    captured_header: dict[str, str | None] = {"authorization": None}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_header["authorization"] = request.headers.get("Authorization")
        return httpx.Response(status_code=200, json={"keys": []})

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test",
        bearer_token="jwt-token",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        client.list_keys()

    assert captured_header["authorization"] == "Bearer jwt-token"


def test_python_sdk_raises_structured_api_error() -> None:
    from quantum_api_sdk import QuantumApiClient, QuantumApiError

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=429,
            headers={"Retry-After": "15", "X-Request-ID": "req_123"},
            json={
                "error": "too_many_requests",
                "message": "Rate limit or quota exceeded.",
                "details": {"retry_after_seconds": 15},
                "request_id": "req_123",
            },
        )

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test",
        api_key="sdk-secret",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        try:
            client.echo_types()
        except QuantumApiError as exc:
            assert exc.status_code == 429
            assert exc.code == "too_many_requests"
            assert exc.request_id == "req_123"
            assert exc.details == {"retry_after_seconds": 15}
            assert exc.headers["retry-after"] == "15"
        else:
            raise AssertionError("QuantumApiError was not raised")


def test_python_sdk_run_qasm_route_and_payload() -> None:
    from quantum_api_sdk import QuantumApiClient

    captured: dict[str, str | dict[str, object] | None] = {
        "path": None,
        "api_key": None,
        "payload": None,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["api_key"] = request.headers.get("X-API-Key")
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            status_code=200,
            json={
                "detected_qasm_version": "2",
                "num_qubits": 1,
                "shots": 32,
                "counts": {"0": 32},
                "backend_mode": "qiskit",
                "statevector": None,
            },
        )

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test",
        api_key="sdk-secret",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        response = client.run_qasm(
            {
                "qasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; x q[0];',
                "shots": 32,
            }
        )

    assert captured["path"] == "/v1/qasm/run"
    assert captured["api_key"] == "sdk-secret"
    assert isinstance(captured["payload"], dict)
    assert captured["payload"] == {
        "qasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; x q[0];',
        "shots": 32,
    }
    assert response["counts"] == {"0": 32}


def test_python_sdk_submit_qasm_job_route() -> None:
    from quantum_api_sdk import QuantumApiClient

    captured: dict[str, str | None] = {"path": None, "api_key": None}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["api_key"] = request.headers.get("X-API-Key")
        return httpx.Response(
            status_code=200,
            json={
                "job_id": "job_123",
                "provider": "ibm",
                "backend_name": "ibm_fake_backend",
                "ibm_profile": None,
                "remote_job_id": "remote-job-123",
                "status": "queued",
                "created_at": "2026-04-08T00:00:00Z",
            },
        )

    transport = httpx.MockTransport(handler)
    with QuantumApiClient(
        base_url="http://example.test",
        api_key="sdk-secret",
        http_client=httpx.Client(transport=transport, timeout=10.0),
    ) as client:
        response = client.submit_qasm_job(
            {
                "provider": "ibm",
                "backend_name": "ibm_fake_backend",
                "qasm": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; x q[0];',
                "shots": 256,
            }
        )

    assert captured["path"] == "/v1/jobs/qasm"
    assert captured["api_key"] == "sdk-secret"
    assert response["status"] == "queued"
