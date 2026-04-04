from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    NatureFermionicMappingPreviewRequest,
    NatureFermionicMappingPreviewResponse,
    NatureGroundStateEnergyRequest,
    NatureGroundStateEnergyResponse,
)
from quantum_api.services.nature.fermionic_mapping_preview import preview_fermionic_mapping
from quantum_api.services.nature.ground_state_energy import compute_ground_state_energy
from quantum_api.services.phase2_errors import Phase2ServiceError

router = APIRouter()


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


@router.post("/nature/fermionic_mapping_preview", response_model=NatureFermionicMappingPreviewResponse)
def nature_fermionic_mapping_preview(
    request_data: NatureFermionicMappingPreviewRequest,
    request: Request,
) -> NatureFermionicMappingPreviewResponse | JSONResponse:
    try:
        payload = preview_fermionic_mapping(request_data)
    except Phase2ServiceError as exc:
        return service_error_response(request, exc)
    return NatureFermionicMappingPreviewResponse.model_validate(payload)
