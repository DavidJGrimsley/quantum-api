from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from quantum_api.config import get_settings
from quantum_api.execution_jobs import ExecutionJobRecord
from quantum_api.ibm_credentials import IBMProfileMetadata, ResolvedIbmCredentials
from quantum_api.key_management import KeyMetadata
from quantum_api.models.api import (
    ApiKeyMetadataResponse,
    ApiKeyPolicyResponse,
    CircuitJobStatusResponse,
    EndpointAuthMode,
    IBMProfileResponse,
    PortfolioEndpoint,
    PortfolioEndpointParameter,
    PortfolioEndpointRequestBody,
    PortfolioEndpointResponse,
)
from quantum_api.services.ibm_provider import resolve_request_ibm_credentials
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.quantum_runtime import runtime


def request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def service_error_response(request: Request, exc: Phase2ServiceError) -> JSONResponse:
    payload = exc.to_payload()
    payload["request_id"] = request_id_from(request)
    return JSONResponse(status_code=exc.status_code, content=payload)


def qiskit_unavailable_response(request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "provider_unavailable",
            "message": "qiskit is unavailable for this endpoint.",
            "details": {"runtime_mode": runtime.mode},
            "request_id": request_id_from(request),
        },
    )


def auth_user_id_from(request: Request) -> str:
    user_id = getattr(request.state, "auth_user_id", None)
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Supabase authentication required")
    return user_id


def api_key_owner_user_id_from(request: Request) -> str | None:
    owner_user_id = getattr(request.state, "api_key_owner_user_id", None)
    if isinstance(owner_user_id, str) and owner_user_id.strip():
        return owner_user_id
    return None


def api_key_id_from(request: Request) -> str:
    api_key_id = getattr(request.state, "api_key_id", None)
    if not isinstance(api_key_id, str) or not api_key_id.strip():
        raise HTTPException(status_code=401, detail="API key authentication required")
    return api_key_id


def event_metadata_from_request(request: Request) -> dict[str, str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    source_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "")
    return {
        "request_id": request_id_from(request),
        "source_ip": source_ip or "unknown",
        "user_agent": request.headers.get("user-agent", ""),
    }


def key_metadata_response(metadata: KeyMetadata) -> ApiKeyMetadataResponse:
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


def ibm_profile_response(metadata: IBMProfileMetadata) -> IBMProfileResponse:
    return IBMProfileResponse(
        profile_id=metadata.profile_id,
        owner_user_id=metadata.owner_user_id,
        profile_name=metadata.profile_name,
        instance=metadata.instance,
        channel=metadata.channel,
        masked_token=metadata.masked_token,
        is_default=metadata.is_default,
        verification_status=metadata.verification_status,
        last_verified_at=metadata.last_verified_at,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
    )


def job_status_response(record: ExecutionJobRecord) -> CircuitJobStatusResponse:
    error = None
    if record.error_payload is not None:
        error = {
            "error": "provider_job_failed" if record.status == "failed" else "provider_job_error",
            "message": str(record.error_payload.get("message", "Provider job failed.")),
            "details": record.error_payload,
        }
    return CircuitJobStatusResponse.model_validate(
        {
            "job_id": record.job_id,
            "provider": record.provider,
            "backend_name": record.backend_name,
            "ibm_profile": record.ibm_profile_name,
            "remote_job_id": record.remote_job_id,
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "completed_at": record.completed_at,
            "error": error,
        }
    )


async def resolve_ibm_credentials(
    request: Request,
    *,
    profile_name: str | None,
    required: bool,
) -> ResolvedIbmCredentials | None:
    owner_user_id = api_key_owner_user_id_from(request)
    return await resolve_request_ibm_credentials(
        owner_user_id=owner_user_id,
        profile_name=profile_name,
        profile_service=request.app.state.ibm_profile_service,
        required=required,
        allow_env_fallback=True,
    )


def decrypt_job_token(request: Request, ciphertext: str) -> str:
    if not ciphertext:
        raise HTTPException(
            status_code=503,
            detail="Stored provider job credentials are unavailable for this environment.",
        )
    profile_service = request.app.state.ibm_profile_service
    return profile_service.decrypt_token(ciphertext)


def request_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def mounted_path_for_request(path: str, *, root_path: str) -> str:
    normalized_root = root_path.rstrip("/")
    if not normalized_root:
        return path
    if path == "/":
        return f"{normalized_root}/"
    return f"{normalized_root}{path}"


def endpoint_display_sort_key(path: str) -> tuple[int, int, str]:
    priority_prefixes = (
        "/v1/gates",
        "/v1/circuits",
        "/v1/list_backends",
        "/v1/transpile",
        "/v1/qasm",
        "/v1/text",
        "/v1/jobs",
        "/v1/algorithms",
        "/v1/optimization",
        "/v1/experiments",
        "/v1/finance",
        "/v1/ml",
        "/v1/nature",
        "/v1/health",
        "/v1/portfolio.json",
        "/v1/keys",
        "/v1/ibm/profiles",
        "/v1/echo-types",
        "/",
    )
    for index, prefix in enumerate(priority_prefixes):
        if path == prefix or path.startswith(f"{prefix}/"):
            return (0, index, path)
    return (1, len(priority_prefixes), path)


def portfolio_auth_mode_for_path(path: str) -> EndpointAuthMode:
    settings = get_settings()
    if settings.requires_user_jwt(path):
        return "bearer_jwt"
    if settings.requires_api_key(path):
        return "api_key"
    return "public"


def resolve_openapi_ref(openapi_schema: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None

    current: Any = openapi_schema
    for segment in ref[2:].split("/"):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)

    return current if isinstance(current, dict) else None


def extract_schema_example(schema: dict[str, Any], openapi_schema: dict[str, Any]) -> Any | None:
    if "example" in schema:
        return schema.get("example")

    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = resolve_openapi_ref(openapi_schema, ref)
        if resolved is not None:
            return extract_schema_example(resolved, openapi_schema)

    for composite_key in ("anyOf", "oneOf", "allOf"):
        options = schema.get(composite_key)
        if isinstance(options, list):
            for option in options:
                if isinstance(option, dict):
                    example = extract_schema_example(option, openapi_schema)
                    if example is not None:
                        return example

    return None


def extract_json_example(content: dict[str, Any] | None, openapi_schema: dict[str, Any]) -> Any | None:
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
        return extract_schema_example(schema, openapi_schema)

    return None


def schema_type_label(schema: dict[str, Any]) -> str:
    if not isinstance(schema, dict):
        return "object"

    ref = schema.get("$ref")
    if isinstance(ref, str):
        return ref.rsplit("/", 1)[-1]

    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        if schema_type == "array":
            items = schema.get("items")
            item_label = schema_type_label(items if isinstance(items, dict) else {})
            return f"array<{item_label}>"
        return schema_type

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        labels = [schema_type_label(item) for item in any_of if isinstance(item, dict)]
        if labels:
            return " | ".join(labels)

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        labels = [schema_type_label(item) for item in one_of if isinstance(item, dict)]
        if labels:
            return " | ".join(labels)

    return "object"


def portfolio_parameters(operation: dict[str, Any]) -> list[PortfolioEndpointParameter] | None:
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
                type=schema_type_label(schema_dict),
                required=bool(raw.get("required", False)),
                description=str(raw.get("description", "")),
                example=example,
                enum=enum_payload,
            )
        )
    return parameters or None


def portfolio_request_body(
    operation: dict[str, Any], openapi_schema: dict[str, Any]
) -> PortfolioEndpointRequestBody | None:
    raw_request_body = operation.get("requestBody")
    if not isinstance(raw_request_body, dict):
        return None
    content = raw_request_body.get("content")
    content_payload = content if isinstance(content, dict) else None
    return PortfolioEndpointRequestBody(
        description=str(raw_request_body.get("description", "Request payload.")),
        example=extract_json_example(content_payload, openapi_schema),
    )


def portfolio_responses(
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
                example=extract_json_example(content_payload, openapi_schema),
            )
        )
    return responses or [PortfolioEndpointResponse(code="200", description="Success")]


def portfolio_endpoints_from_openapi(openapi_schema: dict[str, Any], *, root_path: str = "") -> list[PortfolioEndpoint]:
    raw_paths = openapi_schema.get("paths")
    if not isinstance(raw_paths, dict):
        return []
    api_prefix = get_settings().api_prefix.rstrip("/")

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

    for path in sorted(raw_paths.keys(), key=endpoint_display_sort_key):
        operations = raw_paths.get(path)
        if not isinstance(operations, dict):
            continue
        if not str(path).startswith(api_prefix):
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
                        "path": mounted_path_for_request(str(path), root_path=root_path),
                        "operationPath": str(path),
                        "summary": summary,
                        "description": description,
                        "auth": portfolio_auth_mode_for_path(str(path)),
                        "parameters": portfolio_parameters(raw_operation),
                        "requestBody": portfolio_request_body(raw_operation, openapi_schema),
                        "responses": portfolio_responses(raw_operation, openapi_schema),
                    }
                )
            )

    return endpoints
