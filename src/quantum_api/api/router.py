from __future__ import annotations

from fastapi import APIRouter

from quantum_api.api.auth_routes import router as auth_router
from quantum_api.api.core import router as core_router
from quantum_api.api.jobs import router as jobs_router
from quantum_api.api.phase5 import router as phase5_router
from quantum_api.api.portfolio import router as portfolio_router
from quantum_api.api.runtime_routes import router as runtime_router
from quantum_api.config import get_settings

initial_settings = get_settings()
router = APIRouter(prefix=initial_settings.api_prefix)

router.include_router(portfolio_router)
router.include_router(core_router)
router.include_router(auth_router)
router.include_router(runtime_router)
router.include_router(jobs_router)
router.include_router(phase5_router)
