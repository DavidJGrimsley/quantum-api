from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

TERMINAL_JOB_STATUSES = {"succeeded", "failed", "cancelled"}
DEFAULT_BELL_CIRCUIT = {
    "num_qubits": 2,
    "operations": [
        {"gate": "h", "target": 0},
        {"gate": "cx", "control": 0, "target": 1},
    ],
}


@dataclass(frozen=True)
class VerificationConfig:
    api_base_url: str
    bearer_jwt: str
    ibm_token: str
    ibm_instance: str
    ibm_channel: str = "ibm_quantum_platform"
    profile_name: str | None = None
    backend_name: str | None = None
    poll_interval_seconds: float = 15.0
    timeout_seconds: float = 1800.0
    cleanup: bool = True


@dataclass
class VerificationArtifacts:
    api_base_url: str
    profile_id: str | None = None
    profile_name: str | None = None
    key_id: str | None = None
    raw_key: str | None = None
    backend_name: str | None = None
    job_id: str | None = None
    terminal_status: str | None = None
    final_job_payload: dict[str, Any] | None = None
    result_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    cleanup_actions: list[str] = field(default_factory=list)


class VerificationError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        artifacts: VerificationArtifacts,
        response_payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.artifacts = artifacts
        self.response_payload = response_payload


def _normalize_api_base_url(raw_value: str) -> str:
    normalized = raw_value.strip().rstrip("/")
    if not normalized:
        raise ValueError("API base URL must not be empty.")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _env_default(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {"raw_text": response.text}
    if isinstance(payload, dict):
        return payload
    return {"payload": payload}


def _request_json(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    expected_statuses: set[int],
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    action: str,
    artifacts: VerificationArtifacts,
) -> dict[str, Any]:
    response = client.request(
        method,
        path,
        headers=headers,
        params=params,
        json=json_body,
    )
    payload = _response_payload(response)
    if response.status_code not in expected_statuses:
        expected = ", ".join(str(status) for status in sorted(expected_statuses))
        raise VerificationError(
            (
                f"{action} failed with status {response.status_code}. "
                f"Expected one of: {expected}."
            ),
            artifacts=artifacts,
            response_payload=payload,
        )
    return payload


def _select_backend(
    payload: dict[str, Any],
    *,
    requested_backend: str | None,
    artifacts: VerificationArtifacts,
) -> str:
    backends = payload.get("backends")
    if not isinstance(backends, list) or not backends:
        raise VerificationError(
            "IBM backend listing returned no backends.",
            artifacts=artifacts,
            response_payload=payload,
        )

    if requested_backend is not None:
        for backend in backends:
            if isinstance(backend, dict) and backend.get("name") == requested_backend:
                return requested_backend
        raise VerificationError(
            f"Requested IBM backend '{requested_backend}' was not returned by /list_backends.",
            artifacts=artifacts,
            response_payload=payload,
        )

    for backend in backends:
        if isinstance(backend, dict) and backend.get("is_hardware") is True:
            name = backend.get("name")
            if isinstance(name, str) and name:
                return name

    raise VerificationError(
        "IBM backend listing did not include a hardware backend.",
        artifacts=artifacts,
        response_payload=payload,
    )


def _cleanup_resources(
    client: httpx.Client,
    config: VerificationConfig,
    artifacts: VerificationArtifacts,
) -> None:
    bearer_headers = {"Authorization": f"Bearer {config.bearer_jwt}"}

    if artifacts.key_id:
        revoke_response = client.post(
            f"keys/{artifacts.key_id}/revoke",
            headers=bearer_headers,
        )
        if revoke_response.status_code == 200:
            artifacts.cleanup_actions.append(f"revoked key {artifacts.key_id}")
        else:
            artifacts.cleanup_actions.append(
                f"key revoke returned {revoke_response.status_code}"
            )

        delete_key_response = client.delete(
            f"keys/{artifacts.key_id}",
            headers=bearer_headers,
        )
        if delete_key_response.status_code == 200:
            artifacts.cleanup_actions.append(f"deleted key {artifacts.key_id}")
        else:
            artifacts.cleanup_actions.append(
                f"key delete returned {delete_key_response.status_code}"
            )

    if artifacts.profile_id:
        delete_profile_response = client.delete(
            f"ibm/profiles/{artifacts.profile_id}",
            headers=bearer_headers,
        )
        if delete_profile_response.status_code == 200:
            artifacts.cleanup_actions.append(f"deleted IBM profile {artifacts.profile_id}")
        else:
            artifacts.cleanup_actions.append(
                f"profile delete returned {delete_profile_response.status_code}"
            )


def run_verification(
    config: VerificationConfig,
    *,
    client: httpx.Client | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> VerificationArtifacts:
    artifacts = VerificationArtifacts(api_base_url=config.api_base_url)
    profile_name = config.profile_name or f"phase4-byo-smoke-{uuid.uuid4().hex[:8]}"
    bearer_headers = {"Authorization": f"Bearer {config.bearer_jwt}"}
    close_client = False

    if client is None:
        client = httpx.Client(base_url=config.api_base_url, timeout=30.0)
        close_client = True

    try:
        created_profile = _request_json(
            client,
            "POST",
            "ibm/profiles",
            expected_statuses={200},
            headers=bearer_headers,
            json_body={
                "profile_name": profile_name,
                "token": config.ibm_token,
                "instance": config.ibm_instance,
                "channel": config.ibm_channel,
                "is_default": True,
            },
            action="Create IBM profile",
            artifacts=artifacts,
        )
        artifacts.profile_id = str(created_profile["profile_id"])
        artifacts.profile_name = str(created_profile["profile_name"])

        verified_profile = _request_json(
            client,
            "POST",
            f"ibm/profiles/{artifacts.profile_id}/verify",
            expected_statuses={200},
            headers=bearer_headers,
            action="Verify IBM profile",
            artifacts=artifacts,
        )
        if verified_profile.get("verified") is not True:
            raise VerificationError(
                "IBM profile verification did not return verified=true.",
                artifacts=artifacts,
                response_payload=verified_profile,
            )

        created_key = _request_json(
            client,
            "POST",
            "keys",
            expected_statuses={200},
            headers=bearer_headers,
            json_body={"name": f"phase4-byo-key-{uuid.uuid4().hex[:6]}"},
            action="Create Quantum API key",
            artifacts=artifacts,
        )
        key_payload = created_key.get("key")
        raw_key = created_key.get("raw_key")
        if not isinstance(key_payload, dict) or not isinstance(raw_key, str) or not raw_key:
            raise VerificationError(
                "Quantum API key creation did not return key metadata and raw_key.",
                artifacts=artifacts,
                response_payload=created_key,
            )
        artifacts.key_id = str(key_payload["key_id"])
        artifacts.raw_key = raw_key

        api_key_headers = {"X-API-Key": artifacts.raw_key}
        listed_backends = _request_json(
            client,
            "GET",
            "list_backends",
            expected_statuses={200},
            headers=api_key_headers,
            params={"provider": "ibm"},
            action="List IBM backends",
            artifacts=artifacts,
        )
        artifacts.backend_name = _select_backend(
            listed_backends,
            requested_backend=config.backend_name,
            artifacts=artifacts,
        )

        _request_json(
            client,
            "POST",
            "transpile",
            expected_statuses={200},
            headers=api_key_headers,
            json_body={
                "backend_name": artifacts.backend_name,
                "provider": "ibm",
                "ibm_profile": artifacts.profile_name,
                "circuit": DEFAULT_BELL_CIRCUIT,
                "output_qasm_version": "3",
            },
            action="Transpile Bell circuit for IBM backend",
            artifacts=artifacts,
        )

        submitted_job = _request_json(
            client,
            "POST",
            "jobs/circuits",
            expected_statuses={200},
            headers=api_key_headers,
            json_body={
                "provider": "ibm",
                "backend_name": artifacts.backend_name,
                "ibm_profile": artifacts.profile_name,
                "shots": 128,
                "circuit": DEFAULT_BELL_CIRCUIT,
            },
            action="Submit IBM hardware job",
            artifacts=artifacts,
        )
        artifacts.job_id = str(submitted_job["job_id"])

        deadline = monotonic() + config.timeout_seconds
        while True:
            job_status = _request_json(
                client,
                "GET",
                f"jobs/{artifacts.job_id}",
                expected_statuses={200},
                headers=api_key_headers,
                action="Poll IBM hardware job status",
                artifacts=artifacts,
            )
            artifacts.final_job_payload = job_status
            status = job_status.get("status")
            if isinstance(status, str) and status in TERMINAL_JOB_STATUSES:
                artifacts.terminal_status = status
                break

            if monotonic() >= deadline:
                raise VerificationError(
                    f"Timed out waiting for job {artifacts.job_id} to reach a terminal status.",
                    artifacts=artifacts,
                    response_payload=job_status,
                )
            sleeper(config.poll_interval_seconds)

        if artifacts.terminal_status == "succeeded":
            artifacts.result_payload = _request_json(
                client,
                "GET",
                f"jobs/{artifacts.job_id}/result",
                expected_statuses={200},
                headers=api_key_headers,
                action="Fetch IBM hardware job result",
                artifacts=artifacts,
            )
            return artifacts

        error_payload = None if artifacts.final_job_payload is None else artifacts.final_job_payload.get("error")
        if not isinstance(error_payload, dict):
            raise VerificationError(
                (
                    f"Terminal IBM job status was '{artifacts.terminal_status}' "
                    "without a structured error payload."
                ),
                artifacts=artifacts,
                response_payload=artifacts.final_job_payload,
            )
        artifacts.error_payload = error_payload
        return artifacts
    finally:
        try:
            if config.cleanup:
                _cleanup_resources(client, config, artifacts)
        finally:
            if close_client:
                client.close()


def _print_artifacts(prefix: str, artifacts: VerificationArtifacts) -> None:
    print(prefix)
    print(f"API base URL: {artifacts.api_base_url}")
    if artifacts.profile_name:
        print(f"IBM profile: {artifacts.profile_name} ({artifacts.profile_id})")
    if artifacts.key_id:
        print(f"Quantum API key id: {artifacts.key_id}")
    if artifacts.backend_name:
        print(f"Backend: {artifacts.backend_name}")
    if artifacts.job_id:
        print(f"Job id: {artifacts.job_id}")
    if artifacts.terminal_status:
        print(f"Terminal status: {artifacts.terminal_status}")
    if artifacts.result_payload is not None:
        print("Result payload:")
        print(json.dumps(artifacts.result_payload, indent=2, sort_keys=True))
    if artifacts.error_payload is not None:
        print("Provider error payload:")
        print(json.dumps(artifacts.error_payload, indent=2, sort_keys=True))
    if artifacts.cleanup_actions:
        print("Cleanup:")
        for action in artifacts.cleanup_actions:
            print(f"- {action}")


def build_config_from_args(args: argparse.Namespace) -> VerificationConfig:
    return VerificationConfig(
        api_base_url=_normalize_api_base_url(args.api_base_url),
        bearer_jwt=args.bearer_jwt,
        ibm_token=args.ibm_token,
        ibm_instance=args.ibm_instance,
        ibm_channel=args.ibm_channel,
        profile_name=args.profile_name,
        backend_name=args.backend_name,
        poll_interval_seconds=args.poll_interval_seconds,
        timeout_seconds=args.timeout_seconds,
        cleanup=args.cleanup,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the live BYO IBM Phase 4 flow against a deployed Quantum API instance "
            "using a real bearer JWT and real IBM credentials."
        )
    )
    parser.add_argument(
        "--api-base-url",
        default=_env_default("VERIFY_API_BASE_URL"),
        required=_env_default("VERIFY_API_BASE_URL") is None,
        help="Quantum API base URL. If /v1 is missing, the script appends it.",
    )
    parser.add_argument(
        "--bearer-jwt",
        default=_env_default("VERIFY_BEARER_JWT"),
        required=_env_default("VERIFY_BEARER_JWT") is None,
        help="Bearer JWT used for /v1/keys* and /v1/ibm/profiles* routes.",
    )
    parser.add_argument(
        "--ibm-token",
        default=_env_default("VERIFY_IBM_TOKEN"),
        required=_env_default("VERIFY_IBM_TOKEN") is None,
        help="IBM Runtime API token to store in the verification profile.",
    )
    parser.add_argument(
        "--ibm-instance",
        default=_env_default("VERIFY_IBM_INSTANCE"),
        required=_env_default("VERIFY_IBM_INSTANCE") is None,
        help="IBM instance / CRN for the verification profile.",
    )
    parser.add_argument(
        "--ibm-channel",
        default=_env_default("VERIFY_IBM_CHANNEL", "ibm_quantum_platform"),
        help="IBM channel for the verification profile.",
    )
    parser.add_argument(
        "--profile-name",
        default=_env_default("VERIFY_IBM_PROFILE_NAME"),
        help="Optional fixed IBM profile name. Defaults to a unique temporary name.",
    )
    parser.add_argument(
        "--backend-name",
        default=_env_default("VERIFY_IBM_BACKEND_NAME"),
        help="Optional IBM backend name override. Defaults to the first listed hardware backend.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=float(_env_default("VERIFY_POLL_INTERVAL_SECONDS", "15")),
        help="Seconds between job-status polls.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(_env_default("VERIFY_TIMEOUT_SECONDS", "1800")),
        help="Maximum seconds to wait for the remote IBM job to reach a terminal state.",
    )
    default_cleanup = _env_bool("VERIFY_CLEANUP", True)
    parser.add_argument(
        "--cleanup",
        dest="cleanup",
        action="store_true",
        default=default_cleanup,
        help="Revoke/delete the created key and delete the created IBM profile after the run.",
    )
    parser.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        help="Leave created verification resources in place.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        artifacts = run_verification(build_config_from_args(args))
    except VerificationError as exc:
        _print_artifacts("BYO IBM verification: FAIL", exc.artifacts)
        print(f"Error: {exc}")
        if exc.response_payload is not None:
            print("Response payload:")
            print(json.dumps(exc.response_payload, indent=2, sort_keys=True))
        return 1
    except Exception as exc:
        print("BYO IBM verification: FAIL")
        print(f"Unexpected error: {exc}")
        return 1

    _print_artifacts("BYO IBM verification: PASS", artifacts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
