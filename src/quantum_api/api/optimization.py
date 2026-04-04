from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    OptimizationQaoaRequest,
    OptimizationQaoaResponse,
    OptimizationVqeRequest,
    OptimizationVqeResponse,
)
from quantum_api.services.optimization.qaoa import solve_qaoa
from quantum_api.services.optimization.vqe import solve_vqe
from quantum_api.services.phase2_errors import Phase2ServiceError

router = APIRouter()


@router.post("/optimization/qaoa", response_model=OptimizationQaoaResponse)
def optimization_qaoa(request_data: OptimizationQaoaRequest, request: Request) -> OptimizationQaoaResponse | JSONResponse:
    try:
        payload = solve_qaoa(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationQaoaResponse.model_validate(payload)


@router.post("/optimization/vqe", response_model=OptimizationVqeResponse)
def optimization_vqe(request_data: OptimizationVqeRequest, request: Request) -> OptimizationVqeResponse | JSONResponse:
    try:
        payload = solve_vqe(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationVqeResponse.model_validate(payload)
