from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    OptimizationKnapsackRequest,
    OptimizationKnapsackResponse,
    OptimizationMaxcutRequest,
    OptimizationMaxcutResponse,
    OptimizationQaoaRequest,
    OptimizationQaoaResponse,
    OptimizationTspRequest,
    OptimizationTspResponse,
    OptimizationVqeRequest,
    OptimizationVqeResponse,
)
from quantum_api.services.optimization.knapsack import solve_knapsack
from quantum_api.services.optimization.maxcut import solve_maxcut
from quantum_api.services.optimization.qaoa import solve_qaoa
from quantum_api.services.optimization.tsp import solve_tsp
from quantum_api.services.optimization.vqe import solve_vqe
from quantum_api.services.service_errors import QuantumApiServiceError

router = APIRouter()


@router.post("/optimization/qaoa", response_model=OptimizationQaoaResponse)
def optimization_qaoa(request_data: OptimizationQaoaRequest, request: Request) -> OptimizationQaoaResponse | JSONResponse:
    try:
        payload = solve_qaoa(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationQaoaResponse.model_validate(payload)


@router.post("/optimization/vqe", response_model=OptimizationVqeResponse)
def optimization_vqe(request_data: OptimizationVqeRequest, request: Request) -> OptimizationVqeResponse | JSONResponse:
    try:
        payload = solve_vqe(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationVqeResponse.model_validate(payload)


@router.post("/optimization/maxcut", response_model=OptimizationMaxcutResponse)
def optimization_maxcut(
    request_data: OptimizationMaxcutRequest,
    request: Request,
) -> OptimizationMaxcutResponse | JSONResponse:
    try:
        payload = solve_maxcut(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationMaxcutResponse.model_validate(payload)


@router.post("/optimization/knapsack", response_model=OptimizationKnapsackResponse)
def optimization_knapsack(
    request_data: OptimizationKnapsackRequest,
    request: Request,
) -> OptimizationKnapsackResponse | JSONResponse:
    try:
        payload = solve_knapsack(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationKnapsackResponse.model_validate(payload)


@router.post("/optimization/tsp", response_model=OptimizationTspResponse)
def optimization_tsp(
    request_data: OptimizationTspRequest,
    request: Request,
) -> OptimizationTspResponse | JSONResponse:
    try:
        payload = solve_tsp(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return OptimizationTspResponse.model_validate(payload)
