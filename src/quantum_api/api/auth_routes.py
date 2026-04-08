from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import (
    auth_user_id_from,
    event_metadata_from_request,
    ibm_profile_response,
    key_metadata_response,
    service_error_response,
)
from quantum_api.ibm_credentials import (
    IBMProfileConflictError,
    IBMProfileEncryptionUnavailableError,
    IBMProfileNotFoundError,
)
from quantum_api.key_management import (
    ApiKeyDeleteConflictError,
    ApiKeyLimitExceededError,
    ApiKeyNotFoundError,
)
from quantum_api.models.api import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyDeleteResponse,
    ApiKeyDeleteRevokedResponse,
    ApiKeyListResponse,
    ApiKeyRevokeResponse,
    ApiKeyRotateResponse,
    IBMProfileCreateRequest,
    IBMProfileListResponse,
    IBMProfileResponse,
    IBMProfileUpdateRequest,
    IBMProfileVerifyResponse,
)
from quantum_api.services.ibm_provider import build_ibm_service
from quantum_api.services.service_errors import (
    ProviderCredentialsInvalidError,
    QuantumApiServiceError,
)

router = APIRouter()


@router.get("/keys", response_model=ApiKeyListResponse)
async def list_keys(request: Request) -> ApiKeyListResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    keys = await lifecycle.list_user_keys(owner_user_id=owner_user_id)
    return ApiKeyListResponse(keys=[key_metadata_response(item) for item in keys])


@router.post("/keys", response_model=ApiKeyCreateResponse)
async def create_key(request: Request, payload: ApiKeyCreateRequest) -> ApiKeyCreateResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    try:
        created = await lifecycle.create_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            name=payload.name,
            event_metadata=event_metadata_from_request(request),
        )
    except ApiKeyLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ApiKeyCreateResponse(key=key_metadata_response(created.metadata), raw_key=created.raw_key)


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyRevokeResponse)
async def revoke_key(key_id: str, request: Request) -> ApiKeyRevokeResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    auth_service = request.app.state.auth_service
    try:
        revoked = await lifecycle.revoke_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc

    await auth_service.invalidate_key_prefix(revoked.key_prefix)
    return ApiKeyRevokeResponse(key=key_metadata_response(revoked))


@router.post("/keys/{key_id}/rotate", response_model=ApiKeyRotateResponse)
async def rotate_key(key_id: str, request: Request) -> ApiKeyRotateResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    auth_service = request.app.state.auth_service
    try:
        rotated = await lifecycle.rotate_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc
    except ApiKeyLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await auth_service.invalidate_key_prefix(rotated.previous_metadata.key_prefix)
    await auth_service.invalidate_key_prefix(rotated.new_key.metadata.key_prefix)
    return ApiKeyRotateResponse(
        previous_key=key_metadata_response(rotated.previous_metadata),
        new_key=key_metadata_response(rotated.new_key.metadata),
        raw_key=rotated.new_key.raw_key,
    )


@router.delete("/keys/revoked", response_model=ApiKeyDeleteRevokedResponse)
async def delete_all_revoked_keys(request: Request) -> ApiKeyDeleteRevokedResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    deleted_count = await lifecycle.delete_all_revoked_keys(
        owner_user_id=owner_user_id,
        actor_user_id=owner_user_id,
        event_metadata=event_metadata_from_request(request),
    )
    return ApiKeyDeleteRevokedResponse(deleted_count=deleted_count)


@router.delete("/keys/{key_id}", response_model=ApiKeyDeleteResponse)
async def delete_key(key_id: str, request: Request) -> ApiKeyDeleteResponse:
    owner_user_id = auth_user_id_from(request)
    lifecycle = request.app.state.api_key_lifecycle_service
    try:
        deleted_key_id = await lifecycle.delete_revoked_key(
            owner_user_id=owner_user_id,
            actor_user_id=owner_user_id,
            key_id=key_id,
            event_metadata=event_metadata_from_request(request),
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Key '{exc}' was not found.") from exc
    except ApiKeyDeleteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ApiKeyDeleteResponse(deleted_key_id=deleted_key_id)


@router.get("/ibm/profiles", response_model=IBMProfileListResponse)
async def list_ibm_profiles(request: Request) -> IBMProfileListResponse:
    owner_user_id = auth_user_id_from(request)
    profile_service = request.app.state.ibm_profile_service
    profiles = await profile_service.list_profiles(owner_user_id=owner_user_id)
    return IBMProfileListResponse(profiles=[ibm_profile_response(profile) for profile in profiles])


@router.post("/ibm/profiles", response_model=IBMProfileResponse)
async def create_ibm_profile(request: Request, payload: IBMProfileCreateRequest) -> IBMProfileResponse:
    owner_user_id = auth_user_id_from(request)
    profile_service = request.app.state.ibm_profile_service
    try:
        profile = await profile_service.create_profile(
            owner_user_id=owner_user_id,
            profile_name=payload.profile_name,
            token=payload.token,
            instance=payload.instance,
            channel=payload.channel,
            is_default=payload.is_default,
        )
    except IBMProfileConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ibm_profile_response(profile)


@router.patch("/ibm/profiles/{profile_id}", response_model=IBMProfileResponse)
async def update_ibm_profile(profile_id: str, request: Request, payload: IBMProfileUpdateRequest) -> IBMProfileResponse:
    owner_user_id = auth_user_id_from(request)
    profile_service = request.app.state.ibm_profile_service
    try:
        profile = await profile_service.update_profile(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
            profile_name=payload.profile_name,
            token=payload.token,
            instance=payload.instance,
            channel=payload.channel,
            is_default=payload.is_default,
        )
    except IBMProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"IBM profile '{exc.identifier}' was not found.") from exc
    except IBMProfileConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ibm_profile_response(profile)


@router.delete("/ibm/profiles/{profile_id}")
async def delete_ibm_profile(profile_id: str, request: Request) -> dict[str, object]:
    owner_user_id = auth_user_id_from(request)
    profile_service = request.app.state.ibm_profile_service
    try:
        deleted_profile_id = await profile_service.delete_profile(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
        )
    except IBMProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"IBM profile '{exc.identifier}' was not found.") from exc
    return {"deleted": True, "deleted_profile_id": deleted_profile_id}


@router.post("/ibm/profiles/{profile_id}/verify", response_model=IBMProfileVerifyResponse)
async def verify_ibm_profile(profile_id: str, request: Request) -> IBMProfileVerifyResponse | JSONResponse:
    owner_user_id = auth_user_id_from(request)
    profile_service = request.app.state.ibm_profile_service
    try:
        credentials = await profile_service.get_profile_credentials_by_id(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
        )
    except IBMProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"IBM profile '{exc.identifier}' was not found.") from exc
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        service = build_ibm_service(credentials)
        service.backends()
    except QuantumApiServiceError as exc:
        if isinstance(exc, ProviderCredentialsInvalidError):
            await profile_service.set_verification_status(
                owner_user_id=owner_user_id,
                profile_id=profile_id,
                status="invalid",
                verified_at=None,
            )
        return service_error_response(request, exc)
    except Exception as exc:
        await profile_service.set_verification_status(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
            status="invalid",
            verified_at=None,
        )
        return service_error_response(
            request,
            ProviderCredentialsInvalidError(details={"provider": "ibm", "provider_error": str(exc)}),
        )

    updated = await profile_service.set_verification_status(
        owner_user_id=owner_user_id,
        profile_id=profile_id,
        status="verified",
        verified_at=datetime.now(UTC),
    )
    return IBMProfileVerifyResponse(profile=ibm_profile_response(updated))
