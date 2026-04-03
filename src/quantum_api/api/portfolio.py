from __future__ import annotations

from fastapi import APIRouter, Request, Response

from quantum_api.api.shared import portfolio_endpoints_from_openapi, request_base_url
from quantum_api.config import get_settings
from quantum_api.models.api import PortfolioApiInfo, PortfolioMetadataResponse

router = APIRouter()


@router.get("/portfolio.json", response_model=PortfolioMetadataResponse)
def portfolio_metadata(request: Request, response: Response) -> PortfolioMetadataResponse:
    settings = get_settings()
    request_root = request_base_url(request)
    api_prefix = settings.api_prefix.rstrip("/")
    base_url = f"{request_root}{api_prefix}"
    openapi_schema = request.app.openapi()
    root_path = str(request.scope.get("root_path", ""))
    response.headers["Cache-Control"] = "no-store"

    return PortfolioMetadataResponse.model_validate(
        {
            "api": PortfolioApiInfo.model_validate(
                {
                    "id": "quantum",
                    "name": settings.app_name,
                    "version": settings.app_version,
                    "icon": "quantum",
                    "description": (
                        "Production Quantum API with key lifecycle management and "
                        "runtime endpoints for simulation and transformation workloads."
                    ),
                    "baseUrl": base_url,
                    "docsUrl": f"{request_root}/docs",
                    "healthUrl": f"{base_url}/health",
                    "status": "active",
                    "featured": True,
                    "tags": ["quantum", "simulation", "security", "api"],
                    "uptime": "n/a",
                }
            ),
            "endpoints": portfolio_endpoints_from_openapi(openapi_schema, root_path=root_path),
        }
    )
