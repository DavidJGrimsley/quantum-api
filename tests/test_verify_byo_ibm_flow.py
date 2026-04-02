from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import httpx
import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_byo_ibm_flow.py"
_SPEC = spec_from_file_location("verify_byo_ibm_flow_script", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

VerificationConfig = _MODULE.VerificationConfig
VerificationError = _MODULE.VerificationError
run_verification = _MODULE.run_verification


def _json_response(request: httpx.Request, status_code: int, payload: dict) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=request)


def _build_client(handler) -> httpx.Client:
    return httpx.Client(
        base_url="https://example.test/v1",
        transport=httpx.MockTransport(handler),
    )


def _base_config(*, cleanup: bool) -> VerificationConfig:
    return VerificationConfig(
        api_base_url="https://example.test/v1",
        bearer_jwt="bearer-token",
        ibm_token="ibm-token",
        ibm_instance="ibm-instance",
        cleanup=cleanup,
        poll_interval_seconds=0.0,
        timeout_seconds=30.0,
    )


def test_verify_byo_ibm_flow_success_path():
    poll_counter = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method

        if method == "POST" and path == "/v1/ibm/profiles":
            return _json_response(
                request,
                200,
                {
                    "profile_id": "profile-123",
                    "profile_name": "phase4-byo-smoke-success",
                },
            )
        if method == "POST" and path == "/v1/ibm/profiles/profile-123/verify":
            return _json_response(
                request,
                200,
                {"verified": True, "profile": {"verification_status": "verified"}},
            )
        if method == "POST" and path == "/v1/keys":
            return _json_response(
                request,
                200,
                {
                    "key": {"key_id": "key-123"},
                    "raw_key": "qapi_test_key",
                },
            )
        if method == "GET" and path == "/v1/list_backends":
            return _json_response(
                request,
                200,
                {
                    "backends": [
                        {
                            "name": "ibm_backend_a",
                            "is_hardware": True,
                        }
                    ]
                },
            )
        if method == "POST" and path == "/v1/transpile":
            return _json_response(request, 200, {"provider": "ibm", "backend_name": "ibm_backend_a"})
        if method == "POST" and path == "/v1/jobs/circuits":
            return _json_response(request, 200, {"job_id": "job-123"})
        if method == "GET" and path == "/v1/jobs/job-123":
            poll_counter["count"] += 1
            status = "queued" if poll_counter["count"] == 1 else "succeeded"
            return _json_response(request, 200, {"job_id": "job-123", "status": status})
        if method == "GET" and path == "/v1/jobs/job-123/result":
            return _json_response(
                request,
                200,
                {
                    "job_id": "job-123",
                    "status": "succeeded",
                    "result": {"counts": {"00": 64, "11": 64}},
                },
            )
        raise AssertionError(f"Unexpected request: {method} {path}")

    with _build_client(handler) as client:
        artifacts = run_verification(
            _base_config(cleanup=False),
            client=client,
            sleeper=lambda _: None,
        )

    assert artifacts.backend_name == "ibm_backend_a"
    assert artifacts.job_id == "job-123"
    assert artifacts.terminal_status == "succeeded"
    assert artifacts.result_payload is not None
    assert artifacts.result_payload["result"]["counts"] == {"00": 64, "11": 64}


def test_verify_byo_ibm_flow_terminal_failure_returns_structured_error():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method

        if method == "POST" and path == "/v1/ibm/profiles":
            return _json_response(
                request,
                200,
                {
                    "profile_id": "profile-123",
                    "profile_name": "phase4-byo-smoke-failed",
                },
            )
        if method == "POST" and path == "/v1/ibm/profiles/profile-123/verify":
            return _json_response(
                request,
                200,
                {"verified": True, "profile": {"verification_status": "verified"}},
            )
        if method == "POST" and path == "/v1/keys":
            return _json_response(
                request,
                200,
                {
                    "key": {"key_id": "key-123"},
                    "raw_key": "qapi_test_key",
                },
            )
        if method == "GET" and path == "/v1/list_backends":
            return _json_response(
                request,
                200,
                {
                    "backends": [
                        {
                            "name": "ibm_backend_a",
                            "is_hardware": True,
                        }
                    ]
                },
            )
        if method == "POST" and path == "/v1/transpile":
            return _json_response(request, 200, {"provider": "ibm", "backend_name": "ibm_backend_a"})
        if method == "POST" and path == "/v1/jobs/circuits":
            return _json_response(request, 200, {"job_id": "job-123"})
        if method == "GET" and path == "/v1/jobs/job-123":
            return _json_response(
                request,
                200,
                {
                    "job_id": "job-123",
                    "status": "failed",
                    "error": {
                        "error": "provider_job_failed",
                        "message": "Remote provider rejected the job.",
                    },
                },
            )
        if method == "GET" and path == "/v1/jobs/job-123/result":
            raise AssertionError("Result endpoint should not be called for failed jobs.")
        raise AssertionError(f"Unexpected request: {method} {path}")

    with _build_client(handler) as client:
        artifacts = run_verification(
            _base_config(cleanup=False),
            client=client,
            sleeper=lambda _: None,
        )

    assert artifacts.terminal_status == "failed"
    assert artifacts.result_payload is None
    assert artifacts.error_payload == {
        "error": "provider_job_failed",
        "message": "Remote provider rejected the job.",
    }


def test_verify_byo_ibm_flow_times_out_while_polling():
    class FakeClock:
        def __init__(self) -> None:
            self.value = 0.0

        def __call__(self) -> float:
            self.value += 1.0
            return self.value

    clock = FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method

        if method == "POST" and path == "/v1/ibm/profiles":
            return _json_response(
                request,
                200,
                {
                    "profile_id": "profile-123",
                    "profile_name": "phase4-byo-smoke-timeout",
                },
            )
        if method == "POST" and path == "/v1/ibm/profiles/profile-123/verify":
            return _json_response(
                request,
                200,
                {"verified": True, "profile": {"verification_status": "verified"}},
            )
        if method == "POST" and path == "/v1/keys":
            return _json_response(
                request,
                200,
                {
                    "key": {"key_id": "key-123"},
                    "raw_key": "qapi_test_key",
                },
            )
        if method == "GET" and path == "/v1/list_backends":
            return _json_response(
                request,
                200,
                {
                    "backends": [
                        {
                            "name": "ibm_backend_a",
                            "is_hardware": True,
                        }
                    ]
                },
            )
        if method == "POST" and path == "/v1/transpile":
            return _json_response(request, 200, {"provider": "ibm", "backend_name": "ibm_backend_a"})
        if method == "POST" and path == "/v1/jobs/circuits":
            return _json_response(request, 200, {"job_id": "job-123"})
        if method == "GET" and path == "/v1/jobs/job-123":
            return _json_response(request, 200, {"job_id": "job-123", "status": "running"})
        raise AssertionError(f"Unexpected request: {method} {path}")

    config = VerificationConfig(
        api_base_url="https://example.test/v1",
        bearer_jwt="bearer-token",
        ibm_token="ibm-token",
        ibm_instance="ibm-instance",
        cleanup=False,
        poll_interval_seconds=0.0,
        timeout_seconds=1.0,
    )

    with _build_client(handler) as client, pytest.raises(
        VerificationError,
        match="Timed out waiting for job",
    ):
        run_verification(
            config,
            client=client,
            sleeper=lambda _: None,
            monotonic=clock,
        )


def test_verify_byo_ibm_flow_cleans_up_resources_after_partial_failure():
    recorded_requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append((request.method, request.url.path))
        path = request.url.path
        method = request.method

        if method == "POST" and path == "/v1/ibm/profiles":
            return _json_response(
                request,
                200,
                {
                    "profile_id": "profile-123",
                    "profile_name": "phase4-byo-smoke-cleanup",
                },
            )
        if method == "POST" and path == "/v1/ibm/profiles/profile-123/verify":
            return _json_response(
                request,
                200,
                {"verified": True, "profile": {"verification_status": "verified"}},
            )
        if method == "POST" and path == "/v1/keys":
            return _json_response(
                request,
                200,
                {
                    "key": {"key_id": "key-123"},
                    "raw_key": "qapi_test_key",
                },
            )
        if method == "GET" and path == "/v1/list_backends":
            return _json_response(
                request,
                200,
                {
                    "backends": [
                        {
                            "name": "ibm_backend_a",
                            "is_hardware": True,
                        }
                    ]
                },
            )
        if method == "POST" and path == "/v1/transpile":
            return _json_response(request, 200, {"provider": "ibm", "backend_name": "ibm_backend_a"})
        if method == "POST" and path == "/v1/jobs/circuits":
            return _json_response(
                request,
                503,
                {"error": "provider_unavailable", "message": "IBM provider unavailable."},
            )
        if method == "POST" and path == "/v1/keys/key-123/revoke":
            return _json_response(request, 200, {"key": {"key_id": "key-123", "status": "revoked"}})
        if method == "DELETE" and path == "/v1/keys/key-123":
            return _json_response(request, 200, {"deleted_key_id": "key-123", "deleted": True})
        if method == "DELETE" and path == "/v1/ibm/profiles/profile-123":
            return _json_response(
                request,
                200,
                {"deleted": True, "deleted_profile_id": "profile-123"},
            )
        raise AssertionError(f"Unexpected request: {method} {path}")

    with _build_client(handler) as client, pytest.raises(VerificationError) as exc_info:
        run_verification(
            _base_config(cleanup=True),
            client=client,
            sleeper=lambda _: None,
        )

    assert ("POST", "/v1/keys/key-123/revoke") in recorded_requests
    assert ("DELETE", "/v1/keys/key-123") in recorded_requests
    assert ("DELETE", "/v1/ibm/profiles/profile-123") in recorded_requests
    assert exc_info.value.artifacts.cleanup_actions == [
        "revoked key key-123",
        "deleted key key-123",
        "deleted IBM profile profile-123",
    ]
