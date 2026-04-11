from __future__ import annotations

from quantum_api.main import app
from quantum_api.services.quantum_runtime import runtime
from quantum_api.supabase_auth import AuthenticatedUser

GATEWAY_SERVICE_TOKEN = "gateway-service-test-token"


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


def _create_gateway_context(
    *,
    project_slug: str,
    owner_user_id: str,
    api_key_id: str,
    ibm_profile_id: str | None = None,
    client_key_id: str | None = None,
) -> dict[str, str]:
    headers = {
        "X-Gateway-Service-Token": GATEWAY_SERVICE_TOKEN,
        "X-Gateway-Project-Slug": project_slug,
        "X-Gateway-Owner-User-Id": owner_user_id,
        "X-Gateway-Api-Key-Id": api_key_id,
    }
    if ibm_profile_id is not None:
        headers["X-Gateway-Ibm-Profile-Id"] = ibm_profile_id
    if client_key_id is not None:
        headers["X-Gateway-Client-Key-Id"] = client_key_id
    return headers


def test_internal_gateway_routes_require_service_token(unauth_client):
    response = unauth_client.get("/internal/gateway/v1/health")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"] == "auth_required"
    assert "Gateway service token" in payload["message"]


def test_public_routes_do_not_accept_gateway_service_token(unauth_client):
    response = unauth_client.get("/v1/echo-types", headers={"X-Gateway-Service-Token": GATEWAY_SERVICE_TOKEN})
    assert response.status_code == 401
    assert response.json()["error"] == "auth_required"


def test_internal_gateway_rejects_mismatched_owner_for_api_key_id(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="gateway-owner")
    created_key = unauth_client.post("/v1/keys", json={"name": "gateway-runtime"}, headers=headers)
    assert created_key.status_code == 200
    api_key_id = created_key.json()["key"]["key_id"]

    response = unauth_client.get(
        "/internal/gateway/v1/health",
        headers=_create_gateway_context(
            project_slug="echoes-of-light",
            owner_user_id="different-owner",
            api_key_id=api_key_id,
        ),
    )
    assert response.status_code == 401
    assert response.json()["error"] == "auth_required"


def test_internal_gateway_transpile_uses_gateway_profile_id_context(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="gateway-owner")

    created_profile = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "Gateway IBM",
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
            "is_default": True,
        },
        headers=headers,
    )
    assert created_profile.status_code == 200
    profile_id = created_profile.json()["profile_id"]

    created_key = unauth_client.post("/v1/keys", json={"name": "gateway-runtime"}, headers=headers)
    assert created_key.status_code == 200
    api_key_id = created_key.json()["key"]["key_id"]

    original_qiskit_available = runtime.qiskit_available
    runtime.qiskit_available = True

    def fake_transpile_circuit(request_data, *, ibm_credentials=None):
        assert request_data.provider == "ibm"
        assert ibm_credentials is not None
        assert ibm_credentials.owner_user_id == "gateway-owner"
        assert ibm_credentials.profile_id == profile_id
        assert ibm_credentials.profile_name == "Gateway IBM"
        return {
            "backend_name": request_data.backend_name,
            "provider": "ibm",
            "input_format": "circuit",
            "num_qubits": 1,
            "depth": 1,
            "size": 1,
            "operations": [],
            "qasm_version": "3",
            "qasm": "OPENQASM 3.0;",
        }

    monkeypatch.setattr("quantum_api.api.runtime_routes.transpile_circuit", fake_transpile_circuit)

    try:
        response = unauth_client.post(
            "/internal/gateway/v1/transpile",
            json={
                "backend_name": "ibm_fake_backend",
                "provider": "ibm",
                "circuit": {
                    "num_qubits": 1,
                    "operations": [{"gate": "x", "target": 0}],
                },
            },
            headers=_create_gateway_context(
                project_slug="echoes-of-light",
                owner_user_id="gateway-owner",
                api_key_id=api_key_id,
                ibm_profile_id=profile_id,
                client_key_id="gateway-client-key-1",
            ),
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["provider"] == "ibm"
        assert payload["qasm_version"] == "3"
    finally:
        runtime.qiskit_available = original_qiskit_available
