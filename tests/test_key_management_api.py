from __future__ import annotations

from quantum_api.main import app
from quantum_api.supabase_auth import AuthenticatedUser


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


def test_create_list_revoke_and_rotate_key_flow(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="user-alpha")

    created = unauth_client.post("/v1/keys", json={"name": "primary"}, headers=headers)
    assert created.status_code == 200
    created_payload = created.json()
    raw_key = created_payload["raw_key"]
    key_id = created_payload["key"]["key_id"]
    assert created_payload["secret_visible_once"] is True
    assert created_payload["key"]["status"] == "active"
    assert created_payload["key"]["name"] == "primary"

    listed = unauth_client.get("/v1/keys", headers=headers)
    assert listed.status_code == 200
    listed_payload = listed.json()
    assert any(item["key_id"] == key_id for item in listed_payload["keys"])

    protected_ok = unauth_client.get("/v1/echo-types", headers={"X-API-Key": raw_key})
    assert protected_ok.status_code == 200

    rotated = unauth_client.post(f"/v1/keys/{key_id}/rotate", headers=headers)
    assert rotated.status_code == 200
    rotated_payload = rotated.json()
    new_raw_key = rotated_payload["raw_key"]
    assert rotated_payload["previous_key"]["status"] == "rotated"
    assert rotated_payload["new_key"]["status"] == "active"

    old_key_now_invalid = unauth_client.get("/v1/echo-types", headers={"X-API-Key": raw_key})
    assert old_key_now_invalid.status_code == 401

    new_key_works = unauth_client.get("/v1/echo-types", headers={"X-API-Key": new_raw_key})
    assert new_key_works.status_code == 200

    revoked = unauth_client.post(
        f"/v1/keys/{rotated_payload['new_key']['key_id']}/revoke",
        headers=headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["key"]["status"] == "revoked"

    revoked_now_invalid = unauth_client.get("/v1/echo-types", headers={"X-API-Key": new_raw_key})
    assert revoked_now_invalid.status_code == 401


def test_key_operations_are_user_scoped(unauth_client, monkeypatch):
    owner_headers = _mock_user(monkeypatch, user_id="owner-user")
    created = unauth_client.post("/v1/keys", json={"name": "owner-only"}, headers=owner_headers)
    assert created.status_code == 200
    key_id = created.json()["key"]["key_id"]

    intruder_headers = _mock_user(
        monkeypatch,
        user_id="intruder-user",
        expected_token="Bearer intruder-token",
    )
    forbidden = unauth_client.post(f"/v1/keys/{key_id}/revoke", headers=intruder_headers)
    assert forbidden.status_code == 404
