from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import KernelClassifierRequest, KernelClassifierResponse
from quantum_api.services.machine_learning.kernel_classifier import run_kernel_classifier
from quantum_api.services.phase2_errors import Phase2ServiceError

router = APIRouter()


@router.post("/ml/kernel_classifier", response_model=KernelClassifierResponse)
def ml_kernel_classifier(
    request_data: KernelClassifierRequest,
    request: Request,
) -> KernelClassifierResponse | JSONResponse:
    try:
        payload = run_kernel_classifier(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return KernelClassifierResponse.model_validate(payload)
