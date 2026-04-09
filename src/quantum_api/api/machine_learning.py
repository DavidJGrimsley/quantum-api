from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    KernelClassifierRequest,
    KernelClassifierResponse,
    QsvrRegressorRequest,
    QsvrRegressorResponse,
    VqcClassifierRequest,
    VqcClassifierResponse,
)
from quantum_api.services.machine_learning.kernel_classifier import run_kernel_classifier
from quantum_api.services.machine_learning.qsvr_regressor import run_qsvr_regressor
from quantum_api.services.machine_learning.vqc_classifier import run_vqc_classifier
from quantum_api.services.service_errors import QuantumApiServiceError

router = APIRouter()


@router.post("/ml/kernel_classifier", response_model=KernelClassifierResponse)
async def ml_kernel_classifier(
    request_data: KernelClassifierRequest,
    request: Request,
) -> KernelClassifierResponse | JSONResponse:
    try:
        payload = await run_in_threadpool(run_kernel_classifier, request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return KernelClassifierResponse.model_validate(payload)


@router.post("/ml/vqc_classifier", response_model=VqcClassifierResponse)
async def ml_vqc_classifier(
    request_data: VqcClassifierRequest,
    request: Request,
) -> VqcClassifierResponse | JSONResponse:
    try:
        payload = await run_in_threadpool(run_vqc_classifier, request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return VqcClassifierResponse.model_validate(payload)


@router.post("/ml/qsvr_regressor", response_model=QsvrRegressorResponse)
async def ml_qsvr_regressor(
    request_data: QsvrRegressorRequest,
    request: Request,
) -> QsvrRegressorResponse | JSONResponse:
    try:
        payload = await run_in_threadpool(run_qsvr_regressor, request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return QsvrRegressorResponse.model_validate(payload)
