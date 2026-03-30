from __future__ import annotations

from typing import Any

import httpx

from quantum_api_sdk.types import GateRunResponse, TextTransformResponse


class QuantumApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        response = self._client.request(method, f"{self._base_url}{path}", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def echo_types(self) -> dict[str, Any]:
        return self._request("GET", "/echo-types")

    def run_gate(self, gate_type: str, rotation_angle_rad: float | None = None) -> GateRunResponse:
        payload: dict[str, Any] = {"gate_type": gate_type}
        if rotation_angle_rad is not None:
            payload["rotation_angle_rad"] = rotation_angle_rad

        data = self._request("POST", "/gates/run", payload)
        return GateRunResponse(**data)

    def transform_text(self, text: str) -> TextTransformResponse:
        data = self._request("POST", "/text/transform", {"text": text})
        return TextTransformResponse(**data)
