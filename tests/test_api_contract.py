from fastapi.testclient import TestClient

from quantum_api.config import get_settings
from quantum_api.main import app
from quantum_api.services.quantum_runtime import runtime


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

    by_signature = {
        (item["method"], item["path"]): item
        for item in payload["endpoints"]
    }
    assert ("GET", "/v1/health") in by_signature
    assert ("GET", "/v1/echo-types") in by_signature
    assert ("GET", "/v1/keys") in by_signature
    assert ("GET", "/v1/ibm/profiles") in by_signature
    assert ("POST", "/v1/jobs/circuits") in by_signature
    assert ("GET", "/v1/jobs/{job_id}") in by_signature

    assert by_signature[("GET", "/v1/health")]["auth"] == "public"
    assert by_signature[("GET", "/v1/echo-types")]["auth"] == "api_key"
    assert by_signature[("GET", "/v1/keys")]["auth"] == "bearer_jwt"
    assert by_signature[("GET", "/v1/ibm/profiles")]["auth"] == "bearer_jwt"
    assert by_signature[("POST", "/v1/jobs/circuits")]["auth"] == "api_key"
    assert by_signature[("GET", "/v1/jobs/{job_id}")]["auth"] == "api_key"


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


def test_portfolio_request_body_examples_cover_required_fields(client, unauth_client):
    response = unauth_client.get("/v1/portfolio.json")
    assert response.status_code == 200
    payload = response.json()

    candidate_endpoints = []
    for item in payload["endpoints"]:
        if item.get("method") != "POST":
            continue
        if item.get("auth") not in {"public", "api_key"}:
            continue
        request_body = item.get("requestBody")
        if not isinstance(request_body, dict):
            continue
        if request_body.get("example") is None:
            continue
        candidate_endpoints.append(item)

    assert candidate_endpoints, "Expected POST endpoints with requestBody examples."

    for endpoint in candidate_endpoints:
        post_response = client.post(endpoint["path"], json=endpoint["requestBody"]["example"])
        assert post_response.status_code != 422, (
            f"Example payload missing required fields for {endpoint['path']}: "
            f"{post_response.text}"
        )


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
