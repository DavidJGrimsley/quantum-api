from __future__ import annotations

from typing import Any


class Phase2ServiceError(Exception):
    def __init__(
        self,
        *,
        error: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


class QasmParseError(Phase2ServiceError):
    def __init__(self, *, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            error="qasm_parse_error",
            message=message,
            status_code=400,
            details=details,
        )


class Qasm3DependencyMissingError(Phase2ServiceError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            error="qasm3_dependency_missing",
            message=(
                "OpenQASM 3 import requires optional dependency 'qiskit_qasm3_import'. "
                "Install it to enable QASM3 parsing."
            ),
            status_code=503,
            details=details,
        )


class BackendNotFoundError(Phase2ServiceError):
    def __init__(self, *, backend_name: str, provider: str | None = None) -> None:
        super().__init__(
            error="backend_not_found",
            message=f"Backend '{backend_name}' was not found.",
            status_code=404,
            details={
                "backend_name": backend_name,
                "provider": provider,
            },
        )


class ProviderUnavailableError(Phase2ServiceError):
    def __init__(self, *, provider: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            error="provider_unavailable",
            message=f"Provider '{provider}' is unavailable.",
            status_code=503,
            details=details,
        )


class ProfileNotFoundError(Phase2ServiceError):
    def __init__(self, *, profile_name: str) -> None:
        super().__init__(
            error="profile_not_found",
            message=f"IBM profile '{profile_name}' was not found.",
            status_code=404,
            details={"profile_name": profile_name, "provider": "ibm"},
        )


class ProviderCredentialsMissingError(Phase2ServiceError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            error="provider_credentials_missing",
            message="IBM provider credentials are not configured for this user.",
            status_code=503,
            details=details,
        )


class ProviderCredentialsInvalidError(Phase2ServiceError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            error="provider_credentials_invalid",
            message="Stored IBM provider credentials are invalid.",
            status_code=400,
            details=details,
        )


class JobNotFoundError(Phase2ServiceError):
    def __init__(self, *, job_id: str) -> None:
        super().__init__(
            error="job_not_found",
            message=f"Job '{job_id}' was not found.",
            status_code=404,
            details={"job_id": job_id},
        )


class ResultNotReadyError(Phase2ServiceError):
    def __init__(self, *, job_id: str, status: str) -> None:
        super().__init__(
            error="result_not_ready",
            message=f"Job '{job_id}' has not produced a result yet.",
            status_code=409,
            details={"job_id": job_id, "status": status},
        )
