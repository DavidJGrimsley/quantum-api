from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal, cast

import httpx

from quantum_api_sdk.errors import QuantumApiError, QuantumApiErrorPayload
from quantum_api_sdk.types import (
    AmplitudeEstimationResponse,
    ApiKeyCreateResponse,
    ApiKeyDeleteResponse,
    ApiKeyDeleteRevokedResponse,
    ApiKeyListResponse,
    ApiKeyRevokeResponse,
    ApiKeyRotateResponse,
    AuthMode,
    BackendListResponse,
    CircuitJobResultResponse,
    CircuitJobStatusResponse,
    CircuitJobSubmitResponse,
    CircuitRunResponse,
    EchoTypesResponse,
    FinancePortfolioDiversificationResponse,
    FinancePortfolioOptimizationResponse,
    GateRunResponse,
    GroverSearchResponse,
    HealthResponse,
    IBMProfileListResponse,
    IBMProfileResponse,
    IBMProfileVerifyResponse,
    JsonDict,
    NatureFermionicMappingPreviewResponse,
    NatureGroundStateEnergyResponse,
    OptimizationKnapsackResponse,
    OptimizationMaxcutResponse,
    OptimizationQaoaResponse,
    OptimizationTspResponse,
    OptimizationVqeResponse,
    PhaseEstimationResponse,
    PortfolioMetadata,
    QasmExportResponse,
    QasmImportResponse,
    QuantumVolumeResponse,
    QsvrRegressorResponse,
    RandomizedBenchmarkingResponse,
    StateTomographyResponse,
    T1ExperimentResponse,
    T2RamseyExperimentResponse,
    TextTransformResponse,
    TimeEvolutionResponse,
    TranspileResponse,
    VqcClassifierResponse,
    KernelClassifierResponse,
)

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]


class QuantumApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        api_key: str | None = None,
        bearer_token: str | None = None,
        default_auth_mode: AuthMode = "auto",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = _normalize_base_url(base_url)
        self._api_key = api_key
        self._bearer_token = bearer_token
        self._default_auth_mode = default_auth_mode
        self._client = http_client or httpx.Client(timeout=timeout)

    def __enter__(self) -> QuantumApiClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def health(self, **kwargs: Any) -> HealthResponse:
        return cast(HealthResponse, self._request("GET", "/health", auth="none", **kwargs))

    def portfolio(self, **kwargs: Any) -> PortfolioMetadata:
        return cast(PortfolioMetadata, self._request("GET", "/portfolio.json", auth="none", **kwargs))

    def echo_types(self, **kwargs: Any) -> EchoTypesResponse:
        return cast(EchoTypesResponse, self._request("GET", "/echo-types", **kwargs))

    def run_gate(self, payload: Mapping[str, Any], **kwargs: Any) -> GateRunResponse:
        return cast(GateRunResponse, self._request("POST", "/gates/run", payload=payload, **kwargs))

    def run_circuit(self, payload: Mapping[str, Any], **kwargs: Any) -> CircuitRunResponse:
        return cast(CircuitRunResponse, self._request("POST", "/circuits/run", payload=payload, **kwargs))

    def transform_text(self, payload: Mapping[str, Any], **kwargs: Any) -> TextTransformResponse:
        return cast(TextTransformResponse, self._request("POST", "/text/transform", payload=payload, **kwargs))

    def list_backends(self, *, query: Mapping[str, Any] | None = None, **kwargs: Any) -> BackendListResponse:
        return cast(BackendListResponse, self._request("GET", "/list_backends", query=query, **kwargs))

    def transpile(self, payload: Mapping[str, Any], **kwargs: Any) -> TranspileResponse:
        return cast(TranspileResponse, self._request("POST", "/transpile", payload=payload, **kwargs))

    def import_qasm(self, payload: Mapping[str, Any], **kwargs: Any) -> QasmImportResponse:
        return cast(QasmImportResponse, self._request("POST", "/qasm/import", payload=payload, **kwargs))

    def export_qasm(self, payload: Mapping[str, Any], **kwargs: Any) -> QasmExportResponse:
        return cast(QasmExportResponse, self._request("POST", "/qasm/export", payload=payload, **kwargs))

    def list_keys(self, **kwargs: Any) -> ApiKeyListResponse:
        return cast(ApiKeyListResponse, self._request("GET", "/keys", auth="bearer", **kwargs))

    def create_key(self, payload: Mapping[str, Any], **kwargs: Any) -> ApiKeyCreateResponse:
        return cast(ApiKeyCreateResponse, self._request("POST", "/keys", payload=payload, auth="bearer", **kwargs))

    def revoke_key(self, key_id: str, **kwargs: Any) -> ApiKeyRevokeResponse:
        return cast(
            ApiKeyRevokeResponse,
            self._request("POST", f"/keys/{key_id}/revoke", auth="bearer", **kwargs),
        )

    def rotate_key(self, key_id: str, **kwargs: Any) -> ApiKeyRotateResponse:
        return cast(
            ApiKeyRotateResponse,
            self._request("POST", f"/keys/{key_id}/rotate", auth="bearer", **kwargs),
        )

    def delete_revoked_keys(self, **kwargs: Any) -> ApiKeyDeleteRevokedResponse:
        return cast(
            ApiKeyDeleteRevokedResponse,
            self._request("DELETE", "/keys/revoked", auth="bearer", **kwargs),
        )

    def delete_key(self, key_id: str, **kwargs: Any) -> ApiKeyDeleteResponse:
        return cast(
            ApiKeyDeleteResponse,
            self._request("DELETE", f"/keys/{key_id}", auth="bearer", **kwargs),
        )

    def list_ibm_profiles(self, **kwargs: Any) -> IBMProfileListResponse:
        return cast(IBMProfileListResponse, self._request("GET", "/ibm/profiles", auth="bearer", **kwargs))

    def create_ibm_profile(self, payload: Mapping[str, Any], **kwargs: Any) -> IBMProfileResponse:
        return cast(
            IBMProfileResponse,
            self._request("POST", "/ibm/profiles", payload=payload, auth="bearer", **kwargs),
        )

    def update_ibm_profile(self, profile_id: str, payload: Mapping[str, Any], **kwargs: Any) -> IBMProfileResponse:
        return cast(
            IBMProfileResponse,
            self._request("PATCH", f"/ibm/profiles/{profile_id}", payload=payload, auth="bearer", **kwargs),
        )

    def delete_ibm_profile(self, profile_id: str, **kwargs: Any) -> JsonDict:
        return cast(JsonDict, self._request("DELETE", f"/ibm/profiles/{profile_id}", auth="bearer", **kwargs))

    def verify_ibm_profile(self, profile_id: str, **kwargs: Any) -> IBMProfileVerifyResponse:
        return cast(
            IBMProfileVerifyResponse,
            self._request("POST", f"/ibm/profiles/{profile_id}/verify", auth="bearer", **kwargs),
        )

    def submit_circuit_job(self, payload: Mapping[str, Any], **kwargs: Any) -> CircuitJobSubmitResponse:
        return cast(CircuitJobSubmitResponse, self._request("POST", "/jobs/circuits", payload=payload, **kwargs))

    def get_circuit_job(self, job_id: str, **kwargs: Any) -> CircuitJobStatusResponse:
        return cast(CircuitJobStatusResponse, self._request("GET", f"/jobs/{job_id}", **kwargs))

    def get_circuit_job_result(self, job_id: str, **kwargs: Any) -> CircuitJobResultResponse:
        return cast(CircuitJobResultResponse, self._request("GET", f"/jobs/{job_id}/result", **kwargs))

    def cancel_circuit_job(self, job_id: str, **kwargs: Any) -> CircuitJobStatusResponse:
        return cast(CircuitJobStatusResponse, self._request("POST", f"/jobs/{job_id}/cancel", **kwargs))

    def grover_search(self, payload: Mapping[str, Any], **kwargs: Any) -> GroverSearchResponse:
        return cast(GroverSearchResponse, self._request("POST", "/algorithms/grover_search", payload=payload, **kwargs))

    def amplitude_estimation(self, payload: Mapping[str, Any], **kwargs: Any) -> AmplitudeEstimationResponse:
        return cast(
            AmplitudeEstimationResponse,
            self._request("POST", "/algorithms/amplitude_estimation", payload=payload, **kwargs),
        )

    def phase_estimation(self, payload: Mapping[str, Any], **kwargs: Any) -> PhaseEstimationResponse:
        return cast(
            PhaseEstimationResponse,
            self._request("POST", "/algorithms/phase_estimation", payload=payload, **kwargs),
        )

    def time_evolution(self, payload: Mapping[str, Any], **kwargs: Any) -> TimeEvolutionResponse:
        return cast(TimeEvolutionResponse, self._request("POST", "/algorithms/time_evolution", payload=payload, **kwargs))

    def qaoa(self, payload: Mapping[str, Any], **kwargs: Any) -> OptimizationQaoaResponse:
        return cast(OptimizationQaoaResponse, self._request("POST", "/optimization/qaoa", payload=payload, **kwargs))

    def vqe(self, payload: Mapping[str, Any], **kwargs: Any) -> OptimizationVqeResponse:
        return cast(OptimizationVqeResponse, self._request("POST", "/optimization/vqe", payload=payload, **kwargs))

    def maxcut(self, payload: Mapping[str, Any], **kwargs: Any) -> OptimizationMaxcutResponse:
        return cast(OptimizationMaxcutResponse, self._request("POST", "/optimization/maxcut", payload=payload, **kwargs))

    def knapsack(self, payload: Mapping[str, Any], **kwargs: Any) -> OptimizationKnapsackResponse:
        return cast(
            OptimizationKnapsackResponse,
            self._request("POST", "/optimization/knapsack", payload=payload, **kwargs),
        )

    def tsp(self, payload: Mapping[str, Any], **kwargs: Any) -> OptimizationTspResponse:
        return cast(OptimizationTspResponse, self._request("POST", "/optimization/tsp", payload=payload, **kwargs))

    def state_tomography(self, payload: Mapping[str, Any], **kwargs: Any) -> StateTomographyResponse:
        return cast(
            StateTomographyResponse,
            self._request("POST", "/experiments/state_tomography", payload=payload, **kwargs),
        )

    def randomized_benchmarking(
        self,
        payload: Mapping[str, Any],
        **kwargs: Any,
    ) -> RandomizedBenchmarkingResponse:
        return cast(
            RandomizedBenchmarkingResponse,
            self._request("POST", "/experiments/randomized_benchmarking", payload=payload, **kwargs),
        )

    def quantum_volume(self, payload: Mapping[str, Any], **kwargs: Any) -> QuantumVolumeResponse:
        return cast(QuantumVolumeResponse, self._request("POST", "/experiments/quantum_volume", payload=payload, **kwargs))

    def t1(self, payload: Mapping[str, Any], **kwargs: Any) -> T1ExperimentResponse:
        return cast(T1ExperimentResponse, self._request("POST", "/experiments/t1", payload=payload, **kwargs))

    def t2_ramsey(self, payload: Mapping[str, Any], **kwargs: Any) -> T2RamseyExperimentResponse:
        return cast(T2RamseyExperimentResponse, self._request("POST", "/experiments/t2ramsey", payload=payload, **kwargs))

    def portfolio_optimization(
        self,
        payload: Mapping[str, Any],
        **kwargs: Any,
    ) -> FinancePortfolioOptimizationResponse:
        return cast(
            FinancePortfolioOptimizationResponse,
            self._request("POST", "/finance/portfolio_optimization", payload=payload, **kwargs),
        )

    def portfolio_diversification(
        self,
        payload: Mapping[str, Any],
        **kwargs: Any,
    ) -> FinancePortfolioDiversificationResponse:
        return cast(
            FinancePortfolioDiversificationResponse,
            self._request("POST", "/finance/portfolio_diversification", payload=payload, **kwargs),
        )

    def kernel_classifier(self, payload: Mapping[str, Any], **kwargs: Any) -> KernelClassifierResponse:
        return cast(KernelClassifierResponse, self._request("POST", "/ml/kernel_classifier", payload=payload, **kwargs))

    def vqc_classifier(self, payload: Mapping[str, Any], **kwargs: Any) -> VqcClassifierResponse:
        return cast(VqcClassifierResponse, self._request("POST", "/ml/vqc_classifier", payload=payload, **kwargs))

    def qsvr_regressor(self, payload: Mapping[str, Any], **kwargs: Any) -> QsvrRegressorResponse:
        return cast(QsvrRegressorResponse, self._request("POST", "/ml/qsvr_regressor", payload=payload, **kwargs))

    def ground_state_energy(self, payload: Mapping[str, Any], **kwargs: Any) -> NatureGroundStateEnergyResponse:
        return cast(
            NatureGroundStateEnergyResponse,
            self._request("POST", "/nature/ground_state_energy", payload=payload, **kwargs),
        )

    def fermionic_mapping_preview(
        self,
        payload: Mapping[str, Any],
        **kwargs: Any,
    ) -> NatureFermionicMappingPreviewResponse:
        return cast(
            NatureFermionicMappingPreviewResponse,
            self._request("POST", "/nature/fermionic_mapping_preview", payload=payload, **kwargs),
        )

    def _request(
        self,
        method: HttpMethod,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        query: Mapping[str, Any] | None = None,
        auth: AuthMode | None = None,
        api_key: str | None = None,
        bearer_token: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> JsonDict:
        request_headers: dict[str, str] = dict(headers or {})
        resolved_auth = self._resolve_auth_mode(path, auth)
        resolved_api_key = api_key or self._api_key
        resolved_bearer_token = bearer_token or self._bearer_token

        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        if resolved_auth == "api_key":
            if not resolved_api_key:
                raise ValueError(f"Quantum API request to {path} requires an API key")
            request_headers["X-API-Key"] = resolved_api_key
        elif resolved_auth == "bearer":
            if not resolved_bearer_token:
                raise ValueError(f"Quantum API request to {path} requires a bearer token")
            request_headers["Authorization"] = f"Bearer {resolved_bearer_token}"

        response = self._client.request(
            method,
            f"{self._base_url}{path}",
            params={key: value for key, value in (query or {}).items() if value is not None},
            json=dict(payload) if payload is not None else None,
            headers=request_headers,
        )
        if response.is_success:
            if response.status_code == 204:
                return {}
            return cast(JsonDict, response.json())
        raise _build_api_error(response)

    def _resolve_auth_mode(self, path: str, requested: AuthMode | None) -> Literal["api_key", "bearer", "none"]:
        mode = requested or self._default_auth_mode
        if mode == "api_key":
            return "api_key"
        if mode == "bearer":
            return "bearer"
        if mode == "none":
            return "none"
        if path in {"/health", "/portfolio.json"}:
            return "none"
        if path.startswith("/keys") or path.startswith("/ibm/profiles"):
            return "bearer"
        return "api_key"


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("QuantumApiClient requires a non-empty base_url")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _build_api_error(response: httpx.Response) -> QuantumApiError:
    payload: QuantumApiErrorPayload | None = None
    try:
        raw = response.json()
        if isinstance(raw, dict):
            payload = QuantumApiErrorPayload(
                error=cast(str | None, raw.get("error")),
                message=cast(str | None, raw.get("message")),
                details=raw.get("details"),
                request_id=cast(str | None, raw.get("request_id")),
            )
    except json.JSONDecodeError:
        payload = None

    return QuantumApiError(
        status_code=response.status_code,
        body_text=response.text,
        headers=dict(response.headers),
        payload=payload,
    )
