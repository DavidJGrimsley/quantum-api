from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    FinancePortfolioOptimizationRequest,
    FinancePortfolioOptimizationResponse,
    KernelClassifierRequest,
    KernelClassifierResponse,
    NatureGroundStateEnergyRequest,
    NatureGroundStateEnergyResponse,
    OptimizationQaoaRequest,
    OptimizationQaoaResponse,
    OptimizationVqeRequest,
    OptimizationVqeResponse,
    RandomizedBenchmarkingRequest,
    RandomizedBenchmarkingResponse,
    StateTomographyRequest,
    StateTomographyResponse,
)
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.phase5_experiments import (
    run_randomized_benchmarking,
    run_state_tomography,
)
from quantum_api.services.phase5_finance import solve_portfolio_optimization
from quantum_api.services.phase5_machine_learning import run_kernel_classifier
from quantum_api.services.phase5_nature import compute_ground_state_energy
from quantum_api.services.phase5_optimization import solve_qaoa, solve_vqe

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


@router.post("/experiments/state_tomography", response_model=StateTomographyResponse)
def experiments_state_tomography(
    request_data: StateTomographyRequest,
    request: Request,
) -> StateTomographyResponse | JSONResponse:
    try:
        payload = run_state_tomography(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return StateTomographyResponse.model_validate(payload)


@router.post("/experiments/randomized_benchmarking", response_model=RandomizedBenchmarkingResponse)
def experiments_randomized_benchmarking(
    request_data: RandomizedBenchmarkingRequest,
    request: Request,
) -> RandomizedBenchmarkingResponse | JSONResponse:
    try:
        payload = run_randomized_benchmarking(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return RandomizedBenchmarkingResponse.model_validate(payload)


@router.post("/finance/portfolio_optimization", response_model=FinancePortfolioOptimizationResponse)
def finance_portfolio_optimization(
    request_data: FinancePortfolioOptimizationRequest,
    request: Request,
) -> FinancePortfolioOptimizationResponse | JSONResponse:
    try:
        payload = solve_portfolio_optimization(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return FinancePortfolioOptimizationResponse.model_validate(payload)


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


@router.post("/nature/ground_state_energy", response_model=NatureGroundStateEnergyResponse)
def nature_ground_state_energy(
    request_data: NatureGroundStateEnergyRequest,
    request: Request,
) -> NatureGroundStateEnergyResponse | JSONResponse:
    try:
        payload = compute_ground_state_energy(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return NatureGroundStateEnergyResponse.model_validate(payload)
