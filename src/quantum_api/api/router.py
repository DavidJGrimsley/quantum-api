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

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from quantum_api.config import get_settings
from quantum_api.enums import ECHO_TYPE_DESCRIPTIONS
from quantum_api.models.api import (
    BackendListResponse,
    BackendProvider,
    CircuitRunRequest,
    CircuitRunResponse,
    EchoTypeInfo,
    EchoTypesResponse,
    GateRunRequest,
    GateRunResponse,
    HealthResponse,
    QasmExportRequest,
    QasmExportResponse,
    QasmImportRequest,
    QasmImportResponse,
    TextTransformRequest,
    TextTransformResponse,
    TranspileRequest,
    TranspileResponse,
)
from quantum_api.services.backend_catalog import list_backends
from quantum_api.services.circuit_runner import run_circuit
from quantum_api.services.gate_runner import run_gate
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.text_transform import transform_text
from quantum_api.services.transpilation import (
    export_circuit_to_qasm,
    import_qasm,
    transpile_circuit,
)

initial_settings = get_settings()
router = APIRouter(prefix=initial_settings.api_prefix)


def _phase2_error_response(exc: Phase2ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_payload(),
    )


def _qiskit_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "provider_unavailable",
            "message": "qiskit is unavailable for this endpoint.",
            "details": {"runtime_mode": runtime.mode},
        },
    )


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


@router.get("/list_backends", response_model=BackendListResponse)
def get_backends(
    provider: Annotated[BackendProvider | None, Query()] = None,
    simulator_only: Annotated[bool, Query()] = False,
    min_qubits: Annotated[int, Query(ge=1)] = 1,
) -> BackendListResponse | JSONResponse:
    """List available backends from Aer and optional IBM providers."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response()

    try:
        backends, warnings = list_backends(
            provider=provider,
            simulator_only=simulator_only,
            min_qubits=min_qubits,
        )
    except Phase2ServiceError as exc:
        return _phase2_error_response(exc)

    return BackendListResponse(
        backends=backends,
        total=len(backends),
        filters_applied={
            "provider": provider,
            "simulator_only": simulator_only,
            "min_qubits": min_qubits,
        },
        warnings=warnings or None,
    )


@router.post("/transpile", response_model=TranspileResponse)
def transpile(request: TranspileRequest) -> TranspileResponse | JSONResponse:
    """Transpile a circuit for a selected backend and return normalized output."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response()

    try:
        payload = transpile_circuit(request)
    except Phase2ServiceError as exc:
        return _phase2_error_response(exc)

    return TranspileResponse(**payload)


@router.post("/qasm/import", response_model=QasmImportResponse)
def qasm_import(request: QasmImportRequest) -> QasmImportResponse | JSONResponse:
    """Import OpenQASM and return normalized circuit operation metadata."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response()

    try:
        payload = import_qasm(request)
    except Phase2ServiceError as exc:
        return _phase2_error_response(exc)

    return QasmImportResponse(**payload)


@router.post("/qasm/export", response_model=QasmExportResponse)
def qasm_export(request: QasmExportRequest) -> QasmExportResponse | JSONResponse:
    """Export a JSON-defined circuit as OpenQASM text."""
    if not runtime.qiskit_available:
        return _qiskit_unavailable_response()

    try:
        payload = export_circuit_to_qasm(request)
    except Phase2ServiceError as exc:
        return _phase2_error_response(exc)

    return QasmExportResponse(**payload)


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
