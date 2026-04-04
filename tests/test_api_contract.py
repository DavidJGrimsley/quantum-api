import re
from typing import Any

from fastapi.testclient import TestClient

from quantum_api.config import get_settings
from quantum_api.main import app
from quantum_api.services.quantum_runtime import runtime
from quantum_api.supabase_auth import AuthenticatedUser

_PATH_PARAMETER_RE = re.compile(r"{([^}]+)}")
_ALLOWED_SMOKE_ERROR_STATUSES = {400, 409, 503}


def _mock_bearer_user(
    monkeypatch,
    *,
    user_id: str = "portfolio-smoke-user",
    expected_token: str = "Bearer portfolio-smoke-token",
) -> dict[str, str]:
    async def fake_verify(authorization_header: str | None) -> AuthenticatedUser:
        assert authorization_header == expected_token
        return AuthenticatedUser(
            user_id=user_id,
            email=f"{user_id}@example.test",
            claims={"sub": user_id, "aud": "authenticated"},
        )

    monkeypatch.setattr(app.state.jwt_verifier, "verify_authorization_header", fake_verify)
    return {"Authorization": expected_token}


def _materialize_portfolio_request(
    endpoint: dict[str, Any],
) -> tuple[str, dict[str, Any], Any | None] | None:
    original_path = str(endpoint["path"])
    path = original_path
    parameters = endpoint.get("parameters") or []
    parameters_by_name = {
        str(parameter["name"]): parameter
        for parameter in parameters
        if isinstance(parameter, dict) and "name" in parameter
    }

    for match in _PATH_PARAMETER_RE.finditer(original_path):
        parameter_name = match.group(1)
        parameter = parameters_by_name.get(parameter_name)
        example = None if parameter is None else parameter.get("example")
        if example is None:
            return None
        path = path.replace(f"{{{parameter_name}}}", str(example))

    query_params: dict[str, Any] = {}
    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        parameter_name = str(parameter.get("name", ""))
        if not parameter_name or f"{{{parameter_name}}}" in original_path:
            continue

        example = parameter.get("example")
        if example is None:
            if parameter.get("required"):
                return None
            continue
        query_params[parameter_name] = example

    request_body = None
    request_body_payload = endpoint.get("requestBody")
    if isinstance(request_body_payload, dict):
        request_body = request_body_payload.get("example")
        if request_body is None and str(endpoint["method"]).upper() in {"POST", "PUT", "PATCH"}:
            return None

    if isinstance(request_body, dict):
        request_body = dict(request_body)
        if original_path == "/v1/ibm/profiles" and str(endpoint["method"]).upper() == "POST":
            request_body["profile_name"] = "IBM Portfolio Smoke"
        if original_path == "/v1/keys" and str(endpoint["method"]).upper() == "POST":
            request_body["name"] = "Portfolio smoke key"
        if original_path in {"/v1/jobs/circuits", "/v1/transpile"}:
            request_body.pop("ibm_profile", None)

    return path, query_params, request_body


def test_health_contract(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "Quantum API"
    assert "version" in payload
    assert "qiskit_available" in payload
    assert payload["runtime_mode"] in {"qiskit", "classical-fallback"}


def test_echo_types_contract(client):
    response = client.get("/v1/echo-types")
    assert response.status_code == 200
    payload = response.json()
    assert "echo_types" in payload
    assert any(item["name"] == "quantum_interference" for item in payload["echo_types"])


def test_portfolio_metadata_contract(unauth_client):
    response = unauth_client.get("/v1/portfolio.json")
    assert response.status_code == 200
    payload = response.json()

    assert payload["api"]["id"] == "quantum"
    assert payload["api"]["baseUrl"].endswith("/v1")
    assert payload["api"]["docsUrl"].endswith("/docs")
    assert payload["api"]["healthUrl"].endswith("/v1/health")
    assert response.headers["cache-control"] == "no-store"

    by_signature = {
        (item["method"], item["path"]): item
        for item in payload["endpoints"]
    }
    by_operation_signature = {
        (item["method"], item["operationPath"]): item
        for item in payload["endpoints"]
    }
    assert ("GET", "/v1/health") in by_signature
    assert ("GET", "/v1/echo-types") in by_signature
    assert ("GET", "/v1/keys") in by_signature
    assert ("GET", "/v1/ibm/profiles") in by_signature
    assert ("POST", "/v1/jobs/circuits") in by_signature
    assert ("GET", "/v1/jobs/{job_id}") in by_signature
    assert ("POST", "/v1/optimization/qaoa") in by_signature
    assert ("POST", "/v1/optimization/vqe") in by_signature
    assert ("POST", "/v1/experiments/state_tomography") in by_signature
    assert ("POST", "/v1/experiments/randomized_benchmarking") in by_signature
    assert ("POST", "/v1/finance/portfolio_optimization") in by_signature
    assert ("POST", "/v1/ml/kernel_classifier") in by_signature
    assert ("POST", "/v1/nature/ground_state_energy") in by_signature
    assert by_signature == by_operation_signature
    assert ("GET", "/") not in by_signature

    assert by_signature[("GET", "/v1/health")]["auth"] == "public"
    assert by_signature[("GET", "/v1/echo-types")]["auth"] == "api_key"
    assert by_signature[("GET", "/v1/keys")]["auth"] == "bearer_jwt"
    assert by_signature[("GET", "/v1/ibm/profiles")]["auth"] == "bearer_jwt"
    assert by_signature[("POST", "/v1/jobs/circuits")]["auth"] == "api_key"
    assert by_signature[("GET", "/v1/jobs/{job_id}")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/optimization/qaoa")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/optimization/vqe")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/experiments/state_tomography")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/experiments/randomized_benchmarking")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/finance/portfolio_optimization")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/ml/kernel_classifier")]["auth"] == "api_key"
    assert by_signature[("POST", "/v1/nature/ground_state_energy")]["auth"] == "api_key"


def test_portfolio_metadata_respects_root_path():
    with TestClient(
        app,
        base_url="https://davidjgrimsley.com",
        root_path="/public-facing/api/quantum",
    ) as client:
        response = client.get("/v1/portfolio.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api"]["baseUrl"] == "https://davidjgrimsley.com/public-facing/api/quantum/v1"
    assert payload["api"]["docsUrl"] == "https://davidjgrimsley.com/public-facing/api/quantum/docs"
    assert payload["api"]["healthUrl"] == "https://davidjgrimsley.com/public-facing/api/quantum/v1/health"
    assert response.headers["cache-control"] == "no-store"

    by_signature = {
        (item["method"], item["path"]): item
        for item in payload["endpoints"]
    }
    assert ("GET", "/public-facing/api/quantum/v1/health") in by_signature
    assert ("POST", "/public-facing/api/quantum/v1/optimization/qaoa") in by_signature
    assert ("GET", "/public-facing/api/quantum/") not in by_signature
    assert by_signature[("GET", "/public-facing/api/quantum/v1/health")]["operationPath"] == "/v1/health"
    assert by_signature[("POST", "/public-facing/api/quantum/v1/optimization/qaoa")]["operationPath"] == (
        "/v1/optimization/qaoa"
    )


def test_openapi_declares_security_schemes_for_docs(unauth_client):
    response = unauth_client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()

    security_schemes = payload["components"]["securitySchemes"]
    assert security_schemes["ApiKeyAuth"]["type"] == "apiKey"
    assert security_schemes["ApiKeyAuth"]["in"] == "header"
    assert security_schemes["ApiKeyAuth"]["name"] == "X-API-Key"
    assert security_schemes["BearerAuth"]["type"] == "http"
    assert security_schemes["BearerAuth"]["scheme"] == "bearer"

    assert payload["paths"]["/v1/echo-types"]["get"]["security"] == [{"ApiKeyAuth": []}]
    assert payload["paths"]["/v1/optimization/qaoa"]["post"]["security"] == [{"ApiKeyAuth": []}]
    assert payload["paths"]["/v1/keys"]["get"]["security"] == [{"BearerAuth": []}]
    assert payload["paths"]["/v1/ibm/profiles"]["get"]["security"] == [{"BearerAuth": []}]
    assert "security" not in payload["paths"]["/v1/health"]["get"]
    assert "security" not in payload["paths"]["/v1/portfolio.json"]["get"]


def test_openapi_and_portfolio_drop_auth_requirements_when_auth_is_disabled(unauth_client):
    settings = get_settings()
    original = settings.auth_enabled
    app.openapi_schema = None
    settings.auth_enabled = False
    try:
        openapi_response = unauth_client.get("/openapi.json")
        assert openapi_response.status_code == 200
        openapi_payload = openapi_response.json()
        assert "security" not in openapi_payload["paths"]["/v1/echo-types"]["get"]
        assert "security" not in openapi_payload["paths"]["/v1/optimization/qaoa"]["post"]
        assert "security" not in openapi_payload["paths"]["/v1/keys"]["get"]

        portfolio_response = unauth_client.get("/v1/portfolio.json")
        assert portfolio_response.status_code == 200
        by_signature = {
            (item["method"], item["path"]): item
            for item in portfolio_response.json()["endpoints"]
        }
        assert by_signature[("GET", "/v1/echo-types")]["auth"] == "public"
        assert by_signature[("POST", "/v1/optimization/qaoa")]["auth"] == "public"
        assert by_signature[("GET", "/v1/keys")]["auth"] == "public"
    finally:
        settings.auth_enabled = original
        app.openapi_schema = None


def test_openapi_orders_meta_routes_after_runtime_routes(unauth_client):
    response = unauth_client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()

    ordered_paths = list(payload["paths"].keys())
    assert ordered_paths.index("/v1/algorithms/grover_search") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/optimization/maxcut") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/finance/portfolio_diversification") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/ml/vqc_classifier") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/nature/fermionic_mapping_preview") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/experiments/quantum_volume") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/optimization/qaoa") < ordered_paths.index("/v1/portfolio.json")
    assert ordered_paths.index("/v1/echo-types") > ordered_paths.index("/v1/ibm/profiles")
    assert ordered_paths.index("/v1/nature/ground_state_energy") < ordered_paths.index("/v1/ibm/profiles")


def test_auth_and_cors_respected_with_root_path():
    with TestClient(
        app,
        base_url="https://davidjgrimsley.com",
        root_path="/public-facing/api/quantum",
    ) as client:
        # /v1/echo-types should still require an API key when mounted under a prefix.
        echo_response = client.get(
            "/v1/echo-types",
            headers={"Origin": "https://davidjgrimsley.com"},
        )
        assert echo_response.status_code == 401
        assert "access-control-allow-origin" in {
            k.lower() for k in echo_response.headers
        }

        # Key-management routes (e.g., /v1/keys) should still require JWT when prefixed.
        keys_response = client.get(
            "/v1/keys",
            headers={"Origin": "https://davidjgrimsley.com"},
        )
        assert keys_response.status_code == 401
        assert "access-control-allow-origin" in {
            k.lower() for k in keys_response.headers
        }


def test_portfolio_examples_are_route_valid_for_public_api_key_and_bearer_auth(
    client,
    unauth_client,
    monkeypatch,
):
    bearer_headers = _mock_bearer_user(monkeypatch)
    response = unauth_client.get("/v1/portfolio.json")
    assert response.status_code == 200
    payload = response.json()

    exercised_auth_modes: set[str] = set()
    for item in payload["endpoints"]:
        auth_mode = item.get("auth")
        if auth_mode not in {"public", "api_key", "bearer_jwt"}:
            continue

        materialized = _materialize_portfolio_request(item)
        if materialized is None:
            continue

        path, query_params, request_body = materialized
        request_headers = bearer_headers if auth_mode == "bearer_jwt" else None
        request_client = client if auth_mode == "api_key" else unauth_client

        request_kwargs: dict[str, Any] = {}
        if query_params:
            request_kwargs["params"] = query_params
        if request_body is not None and item["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
            request_kwargs["json"] = request_body

        exercised_auth_modes.add(auth_mode)
        smoke_response = request_client.request(
            item["method"],
            path,
            headers=request_headers,
            **request_kwargs,
        )

        assert smoke_response.status_code not in {404, 405, 422}, (
            f"Portfolio smoke drift for {item['method']} {path}: {smoke_response.text}"
        )
        assert smoke_response.status_code < 300 or smoke_response.status_code in _ALLOWED_SMOKE_ERROR_STATUSES, (
            f"Unexpected smoke status for {item['method']} {path}: "
            f"{smoke_response.status_code} {smoke_response.text}"
        )

    assert exercised_auth_modes == {"public", "api_key", "bearer_jwt"}


def test_gate_run_contract_bit_flip(client):
    response = client.post("/v1/gates/run", json={"gate_type": "bit_flip"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["gate_type"] == "bit_flip"
    assert payload["measurement"] in {0, 1}
    assert isinstance(payload["superposition_strength"], float)
    assert isinstance(payload["success"], bool)


def test_gate_run_rotation_requires_angle(client):
    response = client.post("/v1/gates/run", json={"gate_type": "rotation"})
    assert response.status_code == 422


def test_gate_run_rotation_contract(client):
    response = client.post(
        "/v1/gates/run",
        json={"gate_type": "rotation", "rotation_angle_rad": 1.57079632679},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["gate_type"] == "rotation"
    assert 0.0 <= payload["superposition_strength"] <= 1.0


def test_text_transform_contract(client):
    response = client.post("/v1/text/transform", json={"text": "memory signal and quantum circuit"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["original"]
    assert payload["transformed"]
    assert isinstance(payload["coverage_percent"], float)
    assert isinstance(payload["quantum_words"], int)
    assert isinstance(payload["total_words"], int)
    assert isinstance(payload["category_counts"], dict)


def test_text_transform_validation(client):
    response = client.post("/v1/text/transform", json={})
    assert response.status_code == 422


def test_text_transform_length_guardrail(client):
    max_length = get_settings().max_text_length
    long_text = "a" * (max_length + 1)
    response = client.post("/v1/text/transform", json={"text": long_text})
    assert response.status_code == 422


def test_qiskit_unavailable_mode(client, monkeypatch):
    monkeypatch.setenv("REQUIRE_QISKIT", "true")
    get_settings.cache_clear()

    old_value = runtime.qiskit_available
    runtime.qiskit_available = False

    response = client.post("/v1/gates/run", json={"gate_type": "bit_flip"})
    assert response.status_code == 503

    runtime.qiskit_available = old_value
    monkeypatch.delenv("REQUIRE_QISKIT", raising=False)
    get_settings.cache_clear()


def test_invalid_gate_type(client):
    response = client.post("/v1/gates/run", json={"gate_type": "invalid_gate"})
    assert response.status_code == 422
