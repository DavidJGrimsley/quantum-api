from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import (
    api_key_id_from,
    api_key_owner_user_id_from,
    decrypt_job_token,
    job_status_response,
    resolve_ibm_credentials,
    service_error_response,
)
from quantum_api.execution_jobs import QuantumExecutionJobNotFoundError
from quantum_api.ibm_credentials import IBMProfileEncryptionUnavailableError, ResolvedIbmCredentials
from quantum_api.models.api import (
    CircuitJobResultResponse,
    CircuitJobStatusResponse,
    CircuitJobSubmitRequest,
    CircuitJobSubmitResponse,
)
from quantum_api.services.hardware_jobs import HardwareJobService
from quantum_api.services.phase2_errors import JobNotFoundError, Phase2ServiceError

router = APIRouter()


@router.post("/jobs/circuits", response_model=CircuitJobSubmitResponse)
async def submit_circuit_job(
    request: Request,
    request_data: CircuitJobSubmitRequest,
) -> CircuitJobSubmitResponse | JSONResponse:
    owner_user_id = api_key_owner_user_id_from(request)
    if owner_user_id is None:
        raise HTTPException(status_code=401, detail="API key authentication required")

    try:
        ibm_credentials = await resolve_ibm_credentials(
            request,
            profile_name=request_data.ibm_profile,
            required=True,
        )
        assert ibm_credentials is not None
        if not ibm_credentials.token_ciphertext:
            ibm_credentials = ResolvedIbmCredentials(
                owner_user_id=ibm_credentials.owner_user_id,
                profile_id=ibm_credentials.profile_id,
                profile_name=ibm_credentials.profile_name,
                instance=ibm_credentials.instance,
                channel=ibm_credentials.channel,
                masked_token=ibm_credentials.masked_token,
                token=ibm_credentials.token,
                token_ciphertext=request.app.state.ibm_profile_service.encrypt_token(ibm_credentials.token),
                source=ibm_credentials.source,
            )
        hardware_job_service: HardwareJobService = request.app.state.hardware_job_service
        record = await hardware_job_service.submit_circuit_job(
            owner_user_id=owner_user_id,
            api_key_id=api_key_id_from(request),
            request_data=request_data,
            ibm_credentials=ibm_credentials,
        )
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return CircuitJobSubmitResponse.model_validate(
        {
            "job_id": record.job_id,
            "provider": record.provider,
            "backend_name": record.backend_name,
            "ibm_profile": record.ibm_profile_name,
            "remote_job_id": record.remote_job_id,
            "status": record.status,
            "created_at": record.created_at,
        }
    )


@router.get("/jobs/{job_id}", response_model=CircuitJobStatusResponse)
async def get_circuit_job(job_id: str, request: Request) -> CircuitJobStatusResponse | JSONResponse:
    owner_user_id = api_key_owner_user_id_from(request)
    if owner_user_id is None:
        raise HTTPException(status_code=401, detail="API key authentication required")

    execution_job_service = request.app.state.execution_job_service
    hardware_job_service: HardwareJobService = request.app.state.hardware_job_service
    try:
        record = await execution_job_service.get_job(owner_user_id=owner_user_id, job_id=job_id)
        decrypted_token = decrypt_job_token(request, record.credential_token_ciphertext)
        record = await hardware_job_service.refresh_job(record=record, decrypted_token=decrypted_token)
    except QuantumExecutionJobNotFoundError as exc:
        return service_error_response(request, JobNotFoundError(job_id=exc.job_id))
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return job_status_response(record)


@router.get("/jobs/{job_id}/result", response_model=CircuitJobResultResponse)
async def get_circuit_job_result(job_id: str, request: Request) -> CircuitJobResultResponse | JSONResponse:
    owner_user_id = api_key_owner_user_id_from(request)
    if owner_user_id is None:
        raise HTTPException(status_code=401, detail="API key authentication required")

    execution_job_service = request.app.state.execution_job_service
    hardware_job_service: HardwareJobService = request.app.state.hardware_job_service
    try:
        record = await execution_job_service.get_job(owner_user_id=owner_user_id, job_id=job_id)
        decrypted_token = decrypt_job_token(request, record.credential_token_ciphertext)
        record = await hardware_job_service.refresh_job(record=record, decrypted_token=decrypted_token)
        result_payload = hardware_job_service.assert_result_ready(record)
    except QuantumExecutionJobNotFoundError as exc:
        return service_error_response(request, JobNotFoundError(job_id=exc.job_id))
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return CircuitJobResultResponse.model_validate(
        {
            "job_id": record.job_id,
            "status": "succeeded",
            "result": result_payload,
        }
    )


@router.post("/jobs/{job_id}/cancel", response_model=CircuitJobStatusResponse)
async def cancel_circuit_job(job_id: str, request: Request) -> CircuitJobStatusResponse | JSONResponse:
    owner_user_id = api_key_owner_user_id_from(request)
    if owner_user_id is None:
        raise HTTPException(status_code=401, detail="API key authentication required")

    execution_job_service = request.app.state.execution_job_service
    hardware_job_service: HardwareJobService = request.app.state.hardware_job_service
    try:
        record = await execution_job_service.get_job(owner_user_id=owner_user_id, job_id=job_id)
        decrypted_token = decrypt_job_token(request, record.credential_token_ciphertext)
        record = await hardware_job_service.cancel_job(record=record, decrypted_token=decrypted_token)
    except QuantumExecutionJobNotFoundError as exc:
        return service_error_response(request, JobNotFoundError(job_id=exc.job_id))
    except IBMProfileEncryptionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return job_status_response(record)
