"""Primary HTTP routes for Quantum API.

Current routes are intentionally a minimal, stable core:
- health and capability introspection
- simple gate execution
- multi-qubit circuit execution
- dictionary-driven text transformation

Why these endpoints exist:
- They support current consumer apps immediately (Godot/Expo paths).
- They provide a safe baseline while larger circuit endpoints are being built.
- They establish request/response conventions used by future endpoints.

Planned expansion (tracked in project/TODO.md):
- /transpile
- /list_backends
- QASM import/export
- runtime/hardware jobs and advanced domain modules
"""

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

initial_settings = get_settings()
router = APIRouter(prefix=initial_settings.api_prefix)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service liveness and runtime capability status.

    Purpose:
    - Fast readiness/liveness probe.
    - Tells clients whether qiskit-backed execution is available.
    - Exposes the runtime mode used by computation endpoints.
    """
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
    """Return canonical text-transformation categories.

    Purpose:
    - Provides discoverability for client UIs.
    - Keeps category naming centralized and consistent.
    - Avoids hardcoded transformation labels in client projects.
    """
    payload = [
        EchoTypeInfo(name=echo_type.value, description=description)
        for echo_type, description in ECHO_TYPE_DESCRIPTIONS.items()
    ]
    return EchoTypesResponse(echo_types=payload)


@router.post("/gates/run", response_model=GateRunResponse)
def gates_run(request: GateRunRequest) -> GateRunResponse:
    """Run a single-qubit gate operation and return measurement results.

    Purpose:
    - Provides a low-friction quantum primitive for gameplay/app effects.
    - Supports bit-flip, phase-flip, and rotation (radians).
    - Acts as a stable stepping stone before generalized circuit execution.
    """
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = run_gate(request.gate_type, request.rotation_angle_rad)
    return GateRunResponse(**payload)


@router.post("/circuits/run", response_model=CircuitRunResponse)
def circuits_run(request: CircuitRunRequest) -> CircuitRunResponse:
    """Run a validated multi-qubit circuit and return sampled measurement counts.

    Purpose:
    - Provides a practical multi-qubit execution contract for client workloads.
    - Supports deterministic seeded simulation for reproducible behavior.
    - Optionally returns simulator statevector amplitudes for diagnostics.
    """
    if not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable for /circuits/run",
        )
    payload = run_circuit(request)
    return CircuitRunResponse(**payload)


@router.post("/text/transform", response_model=TextTransformResponse)
def text_transform(request: TextTransformRequest) -> TextTransformResponse:
    """Apply dictionary-driven quantum-style text transformation.

    Purpose:
    - Transforms plain input text based on categorized word behavior.
    - Returns coverage metrics and category counts for diagnostics/UI.
    - Serves current narrative and animation clients with one stable contract.
    """
    settings = get_settings()
    if settings.require_qiskit and not runtime.qiskit_available:
        raise HTTPException(
            status_code=503,
            detail="qiskit is unavailable and REQUIRE_QISKIT=true",
        )
    payload = transform_text(request.text)
    return TextTransformResponse(**payload)
