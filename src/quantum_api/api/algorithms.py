from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    AmplitudeEstimationRequest,
    AmplitudeEstimationResponse,
    GroverSearchRequest,
    GroverSearchResponse,
    PhaseEstimationRequest,
    PhaseEstimationResponse,
    TimeEvolutionRequest,
    TimeEvolutionResponse,
)
from quantum_api.services.algorithms.amplitude_estimation import run_amplitude_estimation
from quantum_api.services.algorithms.grover_search import run_grover_search
from quantum_api.services.algorithms.phase_estimation import run_phase_estimation
from quantum_api.services.algorithms.time_evolution import run_time_evolution
from quantum_api.services.service_errors import QuantumApiServiceError

router = APIRouter()


@router.post("/algorithms/grover_search", response_model=GroverSearchResponse)
def algorithms_grover_search(
    request_data: GroverSearchRequest,
    request: Request,
) -> GroverSearchResponse | JSONResponse:
    try:
        payload = run_grover_search(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return GroverSearchResponse.model_validate(payload)


@router.post("/algorithms/amplitude_estimation", response_model=AmplitudeEstimationResponse)
def algorithms_amplitude_estimation(
    request_data: AmplitudeEstimationRequest,
    request: Request,
) -> AmplitudeEstimationResponse | JSONResponse:
    try:
        payload = run_amplitude_estimation(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return AmplitudeEstimationResponse.model_validate(payload)


@router.post("/algorithms/phase_estimation", response_model=PhaseEstimationResponse)
def algorithms_phase_estimation(
    request_data: PhaseEstimationRequest,
    request: Request,
) -> PhaseEstimationResponse | JSONResponse:
    try:
        payload = run_phase_estimation(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return PhaseEstimationResponse.model_validate(payload)


@router.post("/algorithms/time_evolution", response_model=TimeEvolutionResponse)
def algorithms_time_evolution(
    request_data: TimeEvolutionRequest,
    request: Request,
) -> TimeEvolutionResponse | JSONResponse:
    try:
        payload = run_time_evolution(request_data)
    except QuantumApiServiceError as exc:
        return service_error_response(request, exc)
    return TimeEvolutionResponse.model_validate(payload)
