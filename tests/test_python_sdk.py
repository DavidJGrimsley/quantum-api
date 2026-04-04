from __future__ import annotations

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
