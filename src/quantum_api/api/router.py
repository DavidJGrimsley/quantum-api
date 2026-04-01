"""Primary HTTP routes for Quantum API.

Current routes are intentionally a minimal, stable core:
- health and capability introspection
- simple gate execution
- multi-qubit circuit execution
- dictionary-driven text transformation

Why these endpoints exist:
- They support current consumer apps immediately (Godot/Expo paths).
- They provide a safe baseline while larger circuit endpoints are being built.
- They establish request/response conventions used by future endpoints.

Planned expansion (tracked in project/TODO.md):
- /transpile
- /list_backends
- QASM import/export
- runtime/hardware jobs and advanced domain modules
"""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from quantum_api.config import get_settings
from quantum_api.enums import ECHO_TYPE_DESCRIPTIONS
from quantum_api.key_management import (
    ApiKeyDeleteConflictError,
    ApiKeyLimitExceededError,
    ApiKeyNotFoundError,
    KeyMetadata,
)
from quantum_api.models.api import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyDeleteResponse,
    ApiKeyDeleteRevokedResponse,
    ApiKeyListResponse,
    ApiKeyMetadataResponse,
    ApiKeyPolicyResponse,
    ApiKeyRevokeResponse,
    ApiKeyRotateResponse,
    BackendListResponse,
    BackendProvider,
    CircuitRunRequest,
    CircuitRunResponse,
    EchoTypeInfo,
    EchoTypesResponse,
    GateRunRequest,
    GateRunResponse,
    HealthResponse,
    PortfolioApiInfo,
    PortfolioEndpoint,
    PortfolioEndpointParameter,
    PortfolioEndpointRequestBody,
    PortfolioEndpointResponse,
    PortfolioMetadataResponse,
    QasmExportRequest,
    QasmExportResponse,
    QasmImportRequest,
    QasmImportResponse,
    TextTransformRequest,
    TextTransformResponse,
    TranspileRequest,
    TranspileResponse,
)
from quantum_api.services.backend_catalog import list_backends
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.gate_runner import run_gate
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.text_transform import transform_text
from quantum_api.services.transpilation import (
    export_circuit_to_qasm,
    import_qasm,
    transpile_circuit,
)

initial_settings = get_settings()
router = APIRouter(prefix=initial_settings.api_prefix)


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _phase2_error_response(request: Request, exc: Phase2ServiceError) -> JSONResponse:
    payload = exc.to_payload()
    payload["request_id"] = _request_id_from(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
    )


def _qiskit_unavailable_response(request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "provider_unavailable",
            "message": "qiskit is unavailable for this endpoint.",
            "details": {"runtime_mode": runtime.mode},
            "request_id": _request_id_from(request),
        },
    )


def _auth_user_id_from(request: Request) -> str:
    user_id = getattr(request.state, "auth_user_id", None)
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Supabase authentication required")
    return user_id


def _event_metadata_from_request(request: Request) -> dict[str, str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    source_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "")
    return {
        "request_id": _request_id_from(request),
        "source_ip": source_ip or "unknown",
        "user_agent": request.headers.get("user-agent", ""),
    }


def _key_metadata_response(metadata: KeyMetadata) -> ApiKeyMetadataResponse:
    return ApiKeyMetadataResponse(
        key_id=metadata.key_id,
        owner_user_id=metadata.owner_user_id,
        name=metadata.name,
        key_prefix=metadata.key_prefix,
        masked_key=metadata.masked_key,
        status=metadata.status,
        policy=ApiKeyPolicyResponse(
            rate_limit_per_second=metadata.policy.rate_limit_per_second,
            rate_limit_per_minute=metadata.policy.rate_limit_per_minute,
            daily_quota=metadata.policy.daily_quota,
        ),
        created_at=metadata.created_at,
        revoked_at=metadata.revoked_at,
        rotated_from_id=metadata.rotated_from_id,
        rotated_to_id=metadata.rotated_to_id,
        last_used_at=metadata.last_used_at,
    )


def _request_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _portfolio_auth_mode_for_path(path: str) -> str:
    settings = get_settings()
    if settings.requires_user_jwt(path):
        return "bearer_jwt"
    if settings.requires_api_key(path):
        return "api_key"
    return "public"


def _resolve_openapi_ref(openapi_schema: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None

    current: Any = openapi_schema
    for segment in ref[2:].split("/"):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)

    return current if isinstance(current, dict) else None


def _extract_schema_example(schema: dict[str, Any], openapi_schema: dict[str, Any]) -> Any | None:
    if "example" in schema:
        return schema.get("example")

    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_openapi_ref(openapi_schema, ref)
        if resolved is not None:
            return _extract_schema_example(resolved, openapi_schema)

    for composite_key in ("anyOf", "oneOf", "allOf"):
        options = schema.get(composite_key)
        if isinstance(options, list):
            for option in options:
                if isinstance(option, dict):
                    example = _extract_schema_example(option, openapi_schema)
                    if example is not None:
                        return example

    return None


def _extract_json_example(content: dict[str, Any] | None, openapi_schema: dict[str, Any]) -> Any | None:
    if not isinstance(content, dict):
        return None

    media_candidates = ["application/json", "application/*+json"]
    media_payload: dict[str, Any] | None = None
    for media_type in media_candidates:
        candidate = content.get(media_type)
        if isinstance(candidate, dict):
            media_payload = candidate
            break
    if media_payload is None:
        for candidate in content.values():
            if isinstance(candidate, dict):
                media_payload = candidate
                break

    if not isinstance(media_payload, dict):
        return None

    if "example" in media_payload:
        return media_payload.get("example")

    examples = media_payload.get("examples")
    if isinstance(examples, dict):
        for example_payload in examples.values():
            if isinstance(example_payload, dict) and "value" in example_payload:
                return example_payload.get("value")

    schema = media_payload.get("schema")
    if isinstance(schema, dict):
        return _extract_schema_example(schema, openapi_schema)

    return None


def _schema_type_label(schema: dict[str, Any]) -> str:
    if not isinstance(schema, dict):
        return "object"

    ref = schema.get("$ref")
    if isinstance(ref, str):
        return ref.rsplit("/", 1)[-1]

    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        if schema_type == "array":
            items = schema.get("items")
            item_label = _schema_type_label(items if isinstance(items, dict) else {})
            return f"array<{item_label}>"
        return schema_type

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        labels = [_schema_type_label(item) for item in any_of if isinstance(item, dict)]
        if labels:
            return " | ".join(labels)

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        labels = [_schema_type_label(item) for item in one_of if isinstance(item, dict)]
        if labels:
            return " | ".join(labels)

    return "object"


def _portfolio_parameters(operation: dict[str, Any]) -> list[PortfolioEndpointParameter] | None:
    raw_parameters = operation.get("parameters")
    if not isinstance(raw_parameters, list):
        return None

    parameters: list[PortfolioEndpointParameter] = []
    for raw in raw_parameters:
        if not isinstance(raw, dict):
            continue
        schema = raw.get("schema")
        schema_dict = schema if isinstance(schema, dict) else {}
        example = raw.get("example")
        if example is None:
            example = schema_dict.get("example")
        enum_values = schema_dict.get("enum")
        enum_payload = [str(item) for item in enum_values] if isinstance(enum_values, list) else None
        parameters.append(
            PortfolioEndpointParameter(
                name=str(raw.get("name", "parameter")),
                type=_schema_type_label(schema_dict),
                required=bool(raw.get("required", False)),
                description=str(raw.get("description", "")),
                example=example,
                enum=enum_payload,
            )
        )
    return parameters or None


def _portfolio_request_body(
    operation: dict[str, Any], openapi_schema: dict[str, Any]
) -> PortfolioEndpointRequestBody | None:
    raw_request_body = operation.get("requestBody")
    if not isinstance(raw_request_body, dict):
        return None
    content = raw_request_body.get("content")
    content_payload = content if isinstance(content, dict) else None
    return PortfolioEndpointRequestBody(
        description=str(raw_request_body.get("description", "Request payload.")),
        example=_extract_json_example(content_payload, openapi_schema),
    )


def _portfolio_responses(
    operation: dict[str, Any], openapi_schema: dict[str, Any]
) -> list[PortfolioEndpointResponse]:
    raw_responses = operation.get("responses")
    if not isinstance(raw_responses, dict):
        return [PortfolioEndpointResponse(code="200", description="Success")]

    responses: list[PortfolioEndpointResponse] = []
    for code in sorted(raw_responses.keys(), key=lambda item: str(item)):
        raw = raw_responses.get(code)
        if not isinstance(raw, dict):
            continue
        content = raw.get("content")
        content_payload = content if isinstance(content, dict) else None
        responses.append(
            PortfolioEndpointResponse(
                code=str(code),
                description=str(raw.get("description", "")),
                example=_extract_json_example(content_payload, openapi_schema),
            )
        )
    return responses or [PortfolioEndpointResponse(code="200", description="Success")]


def _portfolio_endpoints_from_openapi(openapi_schema: dict[str, Any]) -> list[PortfolioEndpoint]:
    raw_paths = openapi_schema.get("paths")
    if not isinstance(raw_paths, dict):
        return []

    method_order = {
        "get": 0,
        "post": 1,
        "put": 2,
        "patch": 3,
        "delete": 4,
        "options": 5,
        "head": 6,
    }
    endpoints: list[PortfolioEndpoint] = []

    for path in sorted(raw_paths.keys()):
        operations = raw_paths.get(path)
        if not isinstance(operations, dict):
            continue

        for method in sorted(operations.keys(), key=lambda item: method_order.get(item.lower(), 99)):
            raw_operation = operations.get(method)
            if not isinstance(raw_operation, dict):
                continue
            method_normalized = method.upper()
            if method_normalized not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                continue

            summary = str(raw_operation.get("summary") or f"{method_normalized} {path}")
            description_raw = raw_operation.get("description")
            description = str(description_raw) if isinstance(description_raw, str) else None
            endpoints.append(
                PortfolioEndpoint.model_validate(
                    {
                        "method": method_normalized,
                        "path": str(path),
                        "summary": summary,
                        "description": description,
                        "auth": _portfolio_auth_mode_for_path(str(path)),
                        "parameters": _portfolio_parameters(raw_operation),
                        "requestBody": _portfolio_request_body(raw_operation, openapi_schema),
                        "responses": _portfolio_responses(raw_operation, openapi_schema),
                    }
                )
            )

    return endpoints


@router.get("/portfolio.json", response_model=PortfolioMetadataResponse)
def portfolio_metadata(request: Request) -> PortfolioMetadataResponse:
    """Return dynamic portfolio metadata generated from the current OpenAPI surface."""
    settings = get_settings()
    request_root = _request_base_url(request)
    api_prefix = settings.api_prefix.rstrip("/")
    base_url = f"{request_root}{api_prefix}"
    openapi_schema = request.app.openapi()

    return PortfolioMetadataResponse.model_validate(
        {
            "api": PortfolioApiInfo.model_validate(
                {
                    "id": "quantum",
                    "name": settings.app_name,
                    "version": settings.app_version,
                    "icon": "quantum",
                    "description": (
                        "Production Quantum API with key lifecycle management and "
                        "runtime endpoints for simulation and transformation workloads."
                    ),
                    "baseUrl": base_url,
                    "docsUrl": f"{request_root}/docs",
                    "healthUrl": f"{base_url}/health",
                    "status": "active",
                    "featured": True,
                    "tags": ["quantum", "simulation", "security", "api"],
                    "uptime": "n/a",
                }
            ),
            "endpoints": _portfolio_endpoints_from_openapi(openapi_schema),
        }
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service liveness and runtime capability status.

    Purpose:
    - Fast readiness/liveness probe.
    - Tells clients whether qiskit-backed execution is available.
    - Exposes the runtime mode used by computation endpoints.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        qiskit_available=runtime.qiskit_available,
        runtime_mode=runtime.mode,
    )


@router.get("/echo-types", response_model=EchoTypesResponse)
def echo_types() -> EchoTypesResponse:
    """Return canonical text-transformation categories.

    Purpose:
    - Provides discoverability for client UIs.
    - Keeps category naming centralized and consistent.
    - Avoids hardcoded transformation labels in client projects.
    """
    payload = [
        EchoTypeInfo(name=echo_type.value, description=description)
        for echo_type, description in ECHO_TYPE_DESCRIPTIONS.items()
    ]
    return EchoTypesResponse(echo_types=payload)


@router.get("/keys", response_model=ApiKeyListResponse)
async def list_keys(request: Request) -> ApiKeyListResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    keys = await lifecycle.list_user_keys(owner_user_id=owner_user_id)
    return ApiKeyListResponse(keys=[_key_metadata_response(item) for item in keys])


@router.post("/keys", response_model=ApiKeyCreateResponse)
async def create_key(request: Request, payload: ApiKeyCreateRequest) -> ApiKeyCreateResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    try:
        created = await lifecycle.create_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            name=payload.name,
            event_metadata=_event_metadata_from_request(request),
        )
    except ApiKeyLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ApiKeyCreateResponse(key=_key_metadata_response(created.metadata), raw_key=created.raw_key)


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyRevokeResponse)
async def revoke_key(key_id: str, request: Request) -> ApiKeyRevokeResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    auth_service = request.app.state.auth_service
    try:
        revoked = await lifecycle.revoke_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=_event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc

    await auth_service.invalidate_key_prefix(revoked.key_prefix)
    return ApiKeyRevokeResponse(key=_key_metadata_response(revoked))


@router.post("/keys/{key_id}/rotate", response_model=ApiKeyRotateResponse)
async def rotate_key(key_id: str, request: Request) -> ApiKeyRotateResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    auth_service = request.app.state.auth_service
    try:
        rotated = await lifecycle.rotate_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=_event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc
    except ApiKeyLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await auth_service.invalidate_key_prefix(rotated.previous_metadata.key_prefix)
    await auth_service.invalidate_key_prefix(rotated.new_key.metadata.key_prefix)
    return ApiKeyRotateResponse(
        previous_key=_key_metadata_response(rotated.previous_metadata),
        new_key=_key_metadata_response(rotated.new_key.metadata),
        raw_key=rotated.new_key.raw_key,
    )


@router.delete("/keys/revoked", response_model=ApiKeyDeleteRevokedResponse)
async def delete_all_revoked_keys(request: Request) -> ApiKeyDeleteRevokedResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    deleted_count = await lifecycle.delete_all_revoked_keys(
        owner_user_id=owner_user_id,
        actor_user_id=owner_user_id,
        event_metadata=_event_metadata_from_request(request),
    )
    return ApiKeyDeleteRevokedResponse(deleted_count=deleted_count)


@router.delete("/keys/{key_id}", response_model=ApiKeyDeleteResponse)
async def delete_key(key_id: str, request: Request) -> ApiKeyDeleteResponse:
    owner_user_id = _auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    try:
        deleted_key_id = await lifecycle.delete_revoked_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=_event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc
    except ApiKeyDeleteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ApiKeyDeleteResponse(deleted_key_id=deleted_key_id)


@router.post("/gates/run", response_model=GateRunResponse)
def gates_run(request: GateRunRequest) -> GateRunResponse:
    """Run a single-qubit gate operation and return measurement results.

    Purpose:
    - Provides a low-friction quantum primitive for gameplay/app effects.
    - Supports bit-flip, phase-flip, and rotation (radians).
    - Acts as a stable stepping stone before generalized circuit execution.
    """
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = run_gate(request.gate_type, request.rotation_angle_rad)
    return GateRunResponse.model_validate(payload)


@router.post("/circuits/run", response_model=CircuitRunResponse)
def circuits_run(request: CircuitRunRequest) -> CircuitRunResponse:
    """Run a validated multi-qubit circuit and return sampled measurement counts.

    Purpose:
    - Provides a practical multi-qubit execution contract for client workloads.
    - Supports deterministic seeded simulation for reproducible behavior.
    - Optionally returns simulator statevector amplitudes for diagnostics.
    """
    if not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable for /circuits/run",
        )
    payload = run_circuit(request)
    return CircuitRunResponse.model_validate(payload)


@router.get("/list_backends", response_model=BackendListResponse)
def get_backends(
    request: Request,
    provider: Annotated[BackendProvider | None, Query()] = None,
    simulator_only: Annotated[bool, Query()] = False,
    min_qubits: Annotated[int, Query(ge=1)] = 1,
) -> BackendListResponse | JSONResponse:
    """List available backends from Aer and optional IBM providers."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response(request)

    try:
        backends, warnings = list_backends(
            provider=provider,
            simulator_only=simulator_only,
            min_qubits=min_qubits,
        )
    except Phase2ServiceError as exc:
        return _phase2_error_response(request, exc)

    return BackendListResponse.model_validate(
        {
            "backends": backends,
            "total": len(backends),
            "filters_applied": {
                "provider": provider,
                "simulator_only": simulator_only,
                "min_qubits": min_qubits,
            },
            "warnings": warnings or None,
        }
    )


@router.post("/transpile", response_model=TranspileResponse)
def transpile(request_data: TranspileRequest, request: Request) -> TranspileResponse | JSONResponse:
    """Transpile a circuit for a selected backend and return normalized output."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response(request)

    try:
        payload = transpile_circuit(request_data)
    except Phase2ServiceError as exc:
        return _phase2_error_response(request, exc)

    return TranspileResponse.model_validate(payload)


@router.post("/qasm/import", response_model=QasmImportResponse)
def qasm_import(request_data: QasmImportRequest, request: Request) -> QasmImportResponse | JSONResponse:
    """Import OpenQASM and return normalized circuit operation metadata."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response(request)

    try:
        payload = import_qasm(request_data)
    except Phase2ServiceError as exc:
        return _phase2_error_response(request, exc)

    return QasmImportResponse.model_validate(payload)


@router.post("/qasm/export", response_model=QasmExportResponse)
def qasm_export(request_data: QasmExportRequest, request: Request) -> QasmExportResponse | JSONResponse:
    """Export a JSON-defined circuit as OpenQASM text."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response(request)

    try:
        payload = export_circuit_to_qasm(request_data)
    except Phase2ServiceError as exc:
        return _phase2_error_response(request, exc)

    return QasmExportResponse.model_validate(payload)


@router.post("/text/transform", response_model=TextTransformResponse)
def text_transform(request: TextTransformRequest) -> TextTransformResponse:
    """Apply dictionary-driven quantum-style text transformation.

    Purpose:
    - Transforms plain input text based on categorized word behavior.
    - Returns coverage metrics and category counts for diagnostics/UI.
    - Serves current narrative and animation clients with one stable contract.
    """
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = transform_text(request.text)
    return TextTransformResponse.model_validate(payload)
