from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    QuantumVolumeRequest,
    QuantumVolumeResponse,
    RandomizedBenchmarkingRequest,
    RandomizedBenchmarkingResponse,
    StateTomographyRequest,
    StateTomographyResponse,
    T1ExperimentRequest,
    T1ExperimentResponse,
    T2RamseyExperimentRequest,
    T2RamseyExperimentResponse,
)
from quantum_api.services.experiments.quantum_volume import run_quantum_volume
from quantum_api.services.experiments.randomized_benchmarking import run_randomized_benchmarking
from quantum_api.services.experiments.state_tomography import run_state_tomography
from quantum_api.services.experiments.t1 import run_t1_experiment
from quantum_api.services.experiments.t2ramsey import run_t2ramsey_experiment
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


@router.post("/experiments/quantum_volume", response_model=QuantumVolumeResponse)
def experiments_quantum_volume(
    request_data: QuantumVolumeRequest,
    request: Request,
) -> QuantumVolumeResponse | JSONResponse:
    try:
        payload = run_quantum_volume(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return QuantumVolumeResponse.model_validate(payload)


@router.post("/experiments/t1", response_model=T1ExperimentResponse)
def experiments_t1(
    request_data: T1ExperimentRequest,
    request: Request,
) -> T1ExperimentResponse | JSONResponse:
    try:
        payload = run_t1_experiment(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return T1ExperimentResponse.model_validate(payload)


@router.post("/experiments/t2ramsey", response_model=T2RamseyExperimentResponse)
def experiments_t2ramsey(
    request_data: T2RamseyExperimentRequest,
    request: Request,
) -> T2RamseyExperimentResponse | JSONResponse:
    try:
        payload = run_t2ramsey_experiment(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return T2RamseyExperimentResponse.model_validate(payload)
