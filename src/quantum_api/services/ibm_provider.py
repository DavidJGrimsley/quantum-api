from __future__ import annotations

from functools import lru_cache
from typing import Any

from quantum_api.config import Settings, get_settings
from quantum_api.ibm_credentials import (
    IbmCredentialProfileService,
    IBMDefaultProfileMissingError,
    IBMProfileEncryptionUnavailableError,
    IBMProfileNotFoundError,
    ResolvedIbmCredentials,
    mask_ibm_token,
)
from quantum_api.services.service_errors import (
    ProfileNotFoundError,
    ProviderCredentialsInvalidError,
    ProviderCredentialsMissingError,
    ProviderUnavailableError,
)
from quantum_api.services.quantum_runtime import runtime


def clear_ibm_provider_cache() -> None:
    _build_ibm_service.cache_clear()


async def resolve_request_ibm_credentials(
    *,
    owner_user_id: str | None,
    profile_name: str | None,
    profile_service: IbmCredentialProfileService | None,
    required: bool,
    allow_env_fallback: bool = True,
) -> ResolvedIbmCredentials | None:
    if owner_user_id is not None and profile_service is not None:
        try:
            return await profile_service.resolve_runtime_credentials(
                owner_user_id=owner_user_id,
                profile_name=profile_name,
            )
        except IBMProfileNotFoundError as exc:
            raise ProfileNotFoundError(profile_name=exc.identifier) from exc
        except IBMDefaultProfileMissingError as exc:
            if not allow_env_fallback:
                if required:
                    raise ProviderCredentialsMissingError(
                        details={"reason": "no_default_profile", "provider": "ibm"},
                    ) from exc
                return None
        except IBMProfileEncryptionUnavailableError as exc:
            raise ProviderUnavailableError(
                provider="ibm",
                details={"reason": "profile_encryption_unavailable", "provider_error": str(exc)},
            ) from exc

    settings = get_settings()
    if allow_env_fallback and settings.ibm_is_configured():
        token = settings.ibm_token.strip()
        token_ciphertext = ""
        if profile_service is not None and settings.ibm_profile_encryption_is_configured():
            token_ciphertext = profile_service.encrypt_token(token)
        return ResolvedIbmCredentials(
            owner_user_id=None,
            profile_id=None,
            profile_name=None,
            instance=settings.ibm_instance.strip(),
            channel=settings.ibm_channel.strip(),
            masked_token=mask_ibm_token(token),
            token=token,
            token_ciphertext=token_ciphertext,
            source="server_env",
        )

    if required:
        raise ProviderCredentialsMissingError(
            details={"reason": "missing_credentials", "provider": "ibm"},
        )
    return None


def build_ibm_service(credentials: ResolvedIbmCredentials) -> Any:
    if not runtime.ibm_runtime_available or runtime.QiskitRuntimeService is None:
        raise ProviderUnavailableError(
            provider="ibm",
            details={
                "reason": "missing_dependency",
                "message": "Install qiskit-ibm-runtime to enable IBM provider support.",
                "import_error": runtime.ibm_runtime_import_error,
            },
        )

    try:
        return _build_ibm_service(
            token=credentials.token,
            instance=credentials.instance,
            channel=credentials.channel,
        )
    except ProviderUnavailableError:
        raise
    except Exception as exc:
        raise ProviderCredentialsInvalidError(
            details={"provider": "ibm", "provider_error": str(exc)}
        ) from exc


def normalize_runtime_job_status(raw_status: object) -> str:
    if hasattr(raw_status, "name"):
        status_name = str(raw_status.name).upper()
    else:
        status_name = str(raw_status).upper().split(".")[-1]

    status_map = {
        "INITIALIZING": "queued",
        "QUEUED": "queued",
        "VALIDATING": "queued",
        "RUNNING": "running",
        "DONE": "succeeded",
        "COMPLETED": "succeeded",
        "ERROR": "failed",
        "FAILED": "failed",
        "CANCELLED": "cancelled",
        "CANCELED": "cancelled",
        "CANCELLING": "cancelling",
        "CANCELING": "cancelling",
    }
    return status_map.get(status_name, "queued")


def runtime_job_error_payload(job: Any) -> dict[str, object] | None:
    for attribute in ("error_message", "error"):
        value = getattr(job, attribute, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                value = None
        if value:
            return {"message": str(value)}
    return None


def build_ibm_runtime_service_from_settings(settings: Settings) -> Any:
    credentials = ResolvedIbmCredentials(
        owner_user_id=None,
        profile_id=None,
        profile_name=None,
        instance=settings.ibm_instance.strip(),
        channel=settings.ibm_channel.strip(),
        masked_token=mask_ibm_token(settings.ibm_token.strip()),
        token=settings.ibm_token.strip(),
        token_ciphertext="",
        source="server_env",
    )
    return build_ibm_service(credentials)


@lru_cache
def _build_ibm_service(*, token: str, instance: str, channel: str) -> Any:
    if runtime.QiskitRuntimeService is None:
        raise ProviderUnavailableError(
            provider="ibm",
            details={"reason": "missing_dependency", "import_error": runtime.ibm_runtime_import_error},
        )
    return runtime.QiskitRuntimeService(
        token=token,
        instance=instance,
        channel=channel,
    )
