from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import (
    qiskit_unavailable_response,
    resolve_ibm_credentials,
    service_error_response,
)
from quantum_api.models.api import (
    BackendListResponse,
    BackendProvider,
    QasmExportRequest,
    QasmExportResponse,
    QasmImportRequest,
    QasmImportResponse,
    TranspileRequest,
    TranspileResponse,
)
from quantum_api.services.backend_catalog import list_backends
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.transpilation import (
    export_circuit_to_qasm,
    import_qasm,
    transpile_circuit,
)

router = APIRouter()


@router.get("/list_backends", response_model=BackendListResponse)
async def get_backends(
    request: Request,
    provider: Annotated[BackendProvider | None, Query()] = None,
    simulator_only: Annotated[bool, Query()] = False,
    min_qubits: Annotated[int, Query(ge=1)] = 1,
    ibm_profile: Annotated[str | None, Query()] = None,
) -> BackendListResponse | JSONResponse:
    if not runtime.qiskit_available:
        return qiskit_unavailable_response(request)

    try:
        ibm_credentials = await resolve_ibm_credentials(
            request,
            profile_name=ibm_profile,
            required=provider == "ibm",
        )
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    try:
        backends, warnings = list_backends(
            provider=provider,
            simulator_only=simulator_only,
            min_qubits=min_qubits,
            ibm_credentials=ibm_credentials,
        )
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return BackendListResponse.model_validate(
        {
            "backends": backends,
            "total": len(backends),
            "filters_applied": {
                "provider": provider,
                "simulator_only": simulator_only,
                "min_qubits": min_qubits,
                "ibm_profile": ibm_profile,
            },
            "warnings": warnings or None,
        }
    )


@router.post("/transpile", response_model=TranspileResponse)
async def transpile(request_data: TranspileRequest, request: Request) -> TranspileResponse | JSONResponse:
    if not runtime.qiskit_available:
        return qiskit_unavailable_response(request)

    try:
        ibm_credentials = await resolve_ibm_credentials(
            request,
            profile_name=request_data.ibm_profile,
            required=request_data.provider == "ibm",
        )
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    try:
        payload = transpile_circuit(request_data, ibm_credentials=ibm_credentials)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return TranspileResponse.model_validate(payload)


@router.post("/qasm/import", response_model=QasmImportResponse)
def qasm_import(request_data: QasmImportRequest, request: Request) -> QasmImportResponse | JSONResponse:
    if not runtime.qiskit_available:
        return qiskit_unavailable_response(request)

    try:
        payload = import_qasm(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return QasmImportResponse.model_validate(payload)


@router.post("/qasm/export", response_model=QasmExportResponse)
def qasm_export(request_data: QasmExportRequest, request: Request) -> QasmExportResponse | JSONResponse:
    if not runtime.qiskit_available:
        return qiskit_unavailable_response(request)

    try:
        payload = export_circuit_to_qasm(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)

    return QasmExportResponse.model_validate(payload)
