from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from quantum_api.api.shared import service_error_response
from quantum_api.models.api import (
    FinancePortfolioOptimizationRequest,
    FinancePortfolioOptimizationResponse,
)
from quantum_api.services.finance.portfolio_optimization import solve_portfolio_optimization
from quantum_api.services.phase2_errors import Phase2ServiceError

router = APIRouter()


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
