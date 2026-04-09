from __future__ import annotations

from quantum_api.ibm_credentials import ResolvedIbmCredentials, mask_ibm_token
from quantum_api.services.ibm_provider import build_ibm_service, clear_ibm_provider_cache
from quantum_api.services.quantum_runtime import runtime


def _credentials(token: str) -> ResolvedIbmCredentials:
    return ResolvedIbmCredentials(
        owner_user_id="cache-user",
        profile_id="profile-1",
        profile_name="default",
        instance="instance-a",
        channel="ibm_quantum_platform",
        masked_token=mask_ibm_token(token),
        token=token,
        token_ciphertext="ciphertext",
        source="profile",
    )


def test_build_ibm_service_reuses_cached_instance(monkeypatch):
    created: list[tuple[str, str, str]] = []

    class _FakeRuntimeService:
        def __init__(self, *, token: str, instance: str, channel: str) -> None:
            created.append((token, instance, channel))

    clear_ibm_provider_cache()
    monkeypatch.setattr(runtime, "ibm_runtime_available", True)
    monkeypatch.setattr(runtime, "QiskitRuntimeService", _FakeRuntimeService)

    creds = _credentials("tok_cache_1")
    first = build_ibm_service(creds)
    second = build_ibm_service(creds)

    assert first is second
    assert created == [("tok_cache_1", "instance-a", "ibm_quantum_platform")]


def test_clear_ibm_provider_cache_forces_rebuild(monkeypatch):
    created: list[tuple[str, str, str]] = []

    class _FakeRuntimeService:
        def __init__(self, *, token: str, instance: str, channel: str) -> None:
            created.append((token, instance, channel))

    clear_ibm_provider_cache()
    monkeypatch.setattr(runtime, "ibm_runtime_available", True)
    monkeypatch.setattr(runtime, "QiskitRuntimeService", _FakeRuntimeService)

    creds = _credentials("tok_cache_2")
    first = build_ibm_service(creds)
    clear_ibm_provider_cache()
    second = build_ibm_service(creds)

    assert first is not second
    assert created == [
        ("tok_cache_2", "instance-a", "ibm_quantum_platform"),
        ("tok_cache_2", "instance-a", "ibm_quantum_platform"),
    ]


def test_build_ibm_service_uses_distinct_cache_entries_per_token(monkeypatch):
    created: list[tuple[str, str, str]] = []

    class _FakeRuntimeService:
        def __init__(self, *, token: str, instance: str, channel: str) -> None:
            created.append((token, instance, channel))

    clear_ibm_provider_cache()
    monkeypatch.setattr(runtime, "ibm_runtime_available", True)
    monkeypatch.setattr(runtime, "QiskitRuntimeService", _FakeRuntimeService)

    first = build_ibm_service(_credentials("tok_cache_a"))
    second = build_ibm_service(_credentials("tok_cache_b"))

    assert first is not second
    assert created == [
        ("tok_cache_a", "instance-a", "ibm_quantum_platform"),
        ("tok_cache_b", "instance-a", "ibm_quantum_platform"),
    ]
