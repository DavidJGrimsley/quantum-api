from __future__ import annotations

from types import SimpleNamespace

from quantum_api.main import app
from quantum_api.services.phase2_errors import ProviderUnavailableError
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


def test_ibm_profile_crud_and_verify_flow(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="ibm-user")

    created = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "IBM Open",
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
            "is_default": True,
        },
        headers=headers,
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["profile_name"] == "IBM Open"
    assert created_payload["is_default"] is True
    assert created_payload["masked_token"].endswith("cdef")
    assert "token" not in created_payload

    listed = unauth_client.get("/v1/ibm/profiles", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["profiles"]) == 1

    profile_id = created_payload["profile_id"]
    updated = unauth_client.patch(
        f"/v1/ibm/profiles/{profile_id}",
        json={"profile_name": "IBM Open Renamed"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["profile_name"] == "IBM Open Renamed"
    assert updated.json()["verification_status"] == "unverified"

    monkeypatch.setattr(
        "quantum_api.api.auth_routes.build_ibm_service",
        lambda credentials: SimpleNamespace(backends=lambda: ["ok"]),
    )
    verified = unauth_client.post(f"/v1/ibm/profiles/{profile_id}/verify", headers=headers)
    assert verified.status_code == 200
    assert verified.json()["verified"] is True
    assert verified.json()["profile"]["verification_status"] == "verified"

    deleted = unauth_client.delete(f"/v1/ibm/profiles/{profile_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_ibm_profile_duplicate_name_conflict(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="dup-user")
    payload = {
        "profile_name": "IBM Open",
        "token": "tok_1234567890abcdef",
        "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
    }

    first = unauth_client.post("/v1/ibm/profiles", json=payload, headers=headers)
    second = unauth_client.post("/v1/ibm/profiles", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 409


def test_ibm_profiles_are_user_scoped(unauth_client, monkeypatch):
    owner_headers = _mock_user(monkeypatch, user_id="owner-user")
    created = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "Owner IBM",
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
        },
        headers=owner_headers,
    )
    assert created.status_code == 200
    profile_id = created.json()["profile_id"]

    intruder_headers = _mock_user(
        monkeypatch,
        user_id="intruder-user",
        expected_token="Bearer intruder-token",
    )
    listed = unauth_client.get("/v1/ibm/profiles", headers=intruder_headers)
    assert listed.status_code == 200
    assert listed.json()["profiles"] == []

    rejected = unauth_client.patch(
        f"/v1/ibm/profiles/{profile_id}",
        json={"profile_name": "hijack"},
        headers=intruder_headers,
    )
    assert rejected.status_code == 404


def test_ibm_profile_default_switching(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="default-user")
    first = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "IBM One",
            "token": "tok_aaaaaaaaaaaaaaaa",
            "instance": "instance-one",
        },
        headers=headers,
    )
    second = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "IBM Two",
            "token": "tok_bbbbbbbbbbbbbbbb",
            "instance": "instance-two",
            "is_default": True,
        },
        headers=headers,
    )
    assert first.status_code == 200
    assert second.status_code == 200

    listed = unauth_client.get("/v1/ibm/profiles", headers=headers)
    assert listed.status_code == 200
    by_name = {item["profile_name"]: item for item in listed.json()["profiles"]}
    assert by_name["IBM One"]["is_default"] is False
    assert by_name["IBM Two"]["is_default"] is True


def test_ibm_profile_verify_provider_unavailable_does_not_mark_invalid(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="verify-unavailable-user")
    created = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "IBM Verify",
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
        },
        headers=headers,
    )
    assert created.status_code == 200
    profile_id = created.json()["profile_id"]

    def fail_build(_credentials):
        raise ProviderUnavailableError(provider="ibm", details={"reason": "missing_dependency"})

    monkeypatch.setattr("quantum_api.api.auth_routes.build_ibm_service", fail_build)

    verified = unauth_client.post(f"/v1/ibm/profiles/{profile_id}/verify", headers=headers)
    assert verified.status_code == 503
    assert verified.json()["error"] == "provider_unavailable"

    listed = unauth_client.get("/v1/ibm/profiles", headers=headers)
    assert listed.status_code == 200
    profile = listed.json()["profiles"][0]
    assert profile["verification_status"] == "unverified"
