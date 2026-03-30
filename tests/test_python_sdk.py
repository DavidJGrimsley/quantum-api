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
    client = QuantumApiClient(base_url="http://example.test/v1", api_key="sdk-secret")
    try:
        client._client.close()
        client._client = httpx.Client(transport=transport, timeout=10.0)
        client.health()
        assert captured_header["api_key"] == "sdk-secret"
    finally:
        client.close()
