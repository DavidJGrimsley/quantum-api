from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    RandomizedBenchmarkingRequest,
    RandomizedBenchmarkingResponse,
    StateTomographyRequest,
    StateTomographyResponse,
)
from quantum_api.services.experiments.randomized_benchmarking import run_randomized_benchmarking
from quantum_api.services.experiments.state_tomography import run_state_tomography
from quantum_api.services.phase2_errors import Phase2ServiceError

router = APIRouter()


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
