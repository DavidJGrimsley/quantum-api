from __future__ import annotations

from fastapi import APIRouter, HTTPException

from quantum_api.config import get_settings
from quantum_api.enums import ECHO_TYPE_DESCRIPTIONS
from quantum_api.models.api import (
    CircuitRunRequest,
    CircuitRunResponse,
    EchoTypeInfo,
    EchoTypesResponse,
    GateRunRequest,
    GateRunResponse,
    HealthResponse,
    TextTransformRequest,
    TextTransformResponse,
)
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.gate_runner import run_gate
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.text_transform import transform_text

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        qiskit_available=runtime.qiskit_available,
        runtime_mode=runtime.mode,
    )


@router.get("/echo-types", response_model=EchoTypesResponse)
def echo_types() -> EchoTypesResponse:
    payload = [
        EchoTypeInfo(name=echo_type.value, description=description)
        for echo_type, description in ECHO_TYPE_DESCRIPTIONS.items()
    ]
    return EchoTypesResponse(echo_types=payload)


@router.post("/gates/run", response_model=GateRunResponse)
def gates_run(request: GateRunRequest) -> GateRunResponse:
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = run_gate(request.gate_type, request.rotation_angle_rad)
    return GateRunResponse.model_validate(payload)


@router.post("/circuits/run", response_model=CircuitRunResponse)
def circuits_run(request: CircuitRunRequest) -> CircuitRunResponse:
    if not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable for /circuits/run",
        )
    payload = run_circuit(request)
    return CircuitRunResponse.model_validate(payload)


@router.post("/text/transform", response_model=TextTransformResponse)
def text_transform(request: TextTransformRequest) -> TextTransformResponse:
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = transform_text(request.text)
    return TextTransformResponse.model_validate(payload)
