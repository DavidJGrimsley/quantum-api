from __future__ import annotations

from fastapi import APIRouter

from quantum_api.models.api import TopologicalBraidRequest, TopologicalBraidResponse
from quantum_api.services.topological.braid import run_topological_braid

router = APIRouter()


@router.post("/topological/braid", response_model=TopologicalBraidResponse)
def topological_braid(request_data: TopologicalBraidRequest) -> TopologicalBraidResponse:
    """Evaluate a three-Fibonacci-anyon braid and optionally sample measurement."""

    return TopologicalBraidResponse.model_validate(run_topological_braid(request_data))
