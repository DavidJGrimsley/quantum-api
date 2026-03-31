from __future__ import annotations

from quantum_api.main import app, settings
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


def test_max_active_keys_cap_blocks_extra_creates(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="key-limit-user")
    original_cap = settings.max_active_api_keys_per_user
    settings.max_active_api_keys_per_user = 2

    try:
        first = unauth_client.post("/v1/keys", json={"name": "first"}, headers=headers)
        second = unauth_client.post("/v1/keys", json={"name": "second"}, headers=headers)
        third = unauth_client.post("/v1/keys", json={"name": "third"}, headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 409
        assert "Maximum active API keys reached (2)." in third.json()["message"]
    finally:
        settings.max_active_api_keys_per_user = original_cap


def test_rotate_still_works_when_user_is_at_cap(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="rotate-cap-user")
    original_cap = settings.max_active_api_keys_per_user
    settings.max_active_api_keys_per_user = 2

    try:
        first = unauth_client.post("/v1/keys", json={"name": "first"}, headers=headers)
        second = unauth_client.post("/v1/keys", json={"name": "second"}, headers=headers)
        assert first.status_code == 200
        assert second.status_code == 200

        first_key_id = first.json()["key"]["key_id"]
        rotated = unauth_client.post(f"/v1/keys/{first_key_id}/rotate", headers=headers)
        assert rotated.status_code == 200
        assert rotated.json()["previous_key"]["status"] == "rotated"
        assert rotated.json()["new_key"]["status"] == "active"
    finally:
        settings.max_active_api_keys_per_user = original_cap


def test_max_total_key_history_cap_blocks_extra_creates(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="total-cap-user")
    original_active_cap = settings.max_active_api_keys_per_user
    original_total_cap = settings.max_total_api_keys_per_user
    settings.max_active_api_keys_per_user = 5
    settings.max_total_api_keys_per_user = 2

    try:
        first = unauth_client.post("/v1/keys", json={"name": "first"}, headers=headers)
        second = unauth_client.post("/v1/keys", json={"name": "second"}, headers=headers)
        third = unauth_client.post("/v1/keys", json={"name": "third"}, headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 409
        assert "Maximum total API key history reached (2)." in third.json()["message"]
    finally:
        settings.max_active_api_keys_per_user = original_active_cap
        settings.max_total_api_keys_per_user = original_total_cap


def test_rotate_blocked_when_total_key_history_cap_is_reached(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="total-cap-rotate-user")
    original_active_cap = settings.max_active_api_keys_per_user
    original_total_cap = settings.max_total_api_keys_per_user
    settings.max_active_api_keys_per_user = 5
    settings.max_total_api_keys_per_user = 2

    try:
        first = unauth_client.post("/v1/keys", json={"name": "first"}, headers=headers)
        second = unauth_client.post("/v1/keys", json={"name": "second"}, headers=headers)
        assert first.status_code == 200
        assert second.status_code == 200

        rotate = unauth_client.post(f"/v1/keys/{first.json()['key']['key_id']}/rotate", headers=headers)
        assert rotate.status_code == 409
        assert "Maximum total API key history reached (2)." in rotate.json()["message"]
    finally:
        settings.max_active_api_keys_per_user = original_active_cap
        settings.max_total_api_keys_per_user = original_total_cap


def test_delete_revoked_key_succeeds_and_removes_it_from_list(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="delete-revoked-user")
    created = unauth_client.post("/v1/keys", json={"name": "to-delete"}, headers=headers)
    assert created.status_code == 200
    key_id = created.json()["key"]["key_id"]

    revoked = unauth_client.post(f"/v1/keys/{key_id}/revoke", headers=headers)
    assert revoked.status_code == 200

    deleted = unauth_client.delete(f"/v1/keys/{key_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert deleted.json()["deleted_key_id"] == key_id

    listed = unauth_client.get("/v1/keys", headers=headers)
    assert listed.status_code == 200
    assert all(item["key_id"] != key_id for item in listed.json()["keys"])


def test_delete_active_key_is_rejected(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="delete-active-user")
    created = unauth_client.post("/v1/keys", json={"name": "still-active"}, headers=headers)
    assert created.status_code == 200
    key_id = created.json()["key"]["key_id"]

    rejected = unauth_client.delete(f"/v1/keys/{key_id}", headers=headers)
    assert rejected.status_code == 409
    assert "Only revoked keys can be deleted." in rejected.json()["message"]


def test_delete_all_revoked_keys_only_removes_revoked_records(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="bulk-delete-user")
    first = unauth_client.post("/v1/keys", json={"name": "first"}, headers=headers)
    second = unauth_client.post("/v1/keys", json={"name": "second"}, headers=headers)
    third = unauth_client.post("/v1/keys", json={"name": "third"}, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200

    first_id = first.json()["key"]["key_id"]
    second_id = second.json()["key"]["key_id"]
    third_id = third.json()["key"]["key_id"]

    assert unauth_client.post(f"/v1/keys/{first_id}/revoke", headers=headers).status_code == 200
    assert unauth_client.post(f"/v1/keys/{second_id}/revoke", headers=headers).status_code == 200

    deleted = unauth_client.delete("/v1/keys/revoked", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted_count"] == 2

    listed = unauth_client.get("/v1/keys", headers=headers)
    assert listed.status_code == 200
    remaining_ids = {item["key_id"] for item in listed.json()["keys"]}
    assert third_id in remaining_ids
    assert first_id not in remaining_ids
    assert second_id not in remaining_ids


def test_delete_key_is_user_scoped(unauth_client, monkeypatch):
    owner_headers = _mock_user(monkeypatch, user_id="owner-delete-user")
    created = unauth_client.post("/v1/keys", json={"name": "owner-key"}, headers=owner_headers)
    assert created.status_code == 200
    key_id = created.json()["key"]["key_id"]
    assert unauth_client.post(f"/v1/keys/{key_id}/revoke", headers=owner_headers).status_code == 200

    intruder_headers = _mock_user(
        monkeypatch,
        user_id="intruder-delete-user",
        expected_token="Bearer intruder-delete-token",
    )
    forbidden = unauth_client.delete(f"/v1/keys/{key_id}", headers=intruder_headers)
    assert forbidden.status_code == 404
