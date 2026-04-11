from __future__ import annotations

from fastapi import APIRouter

from quantum_api.api.algorithms import router as algorithms_router
from quantum_api.api.auth_routes import router as auth_router
from quantum_api.api.core import router as core_router
from quantum_api.api.experiments import router as experiments_router
from quantum_api.api.finance import router as finance_router
from quantum_api.api.jobs import router as jobs_router
from quantum_api.api.machine_learning import router as machine_learning_router
from quantum_api.api.nature import router as nature_router
from quantum_api.api.optimization import router as optimization_router
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
router.include_router(algorithms_router)
router.include_router(optimization_router)
router.include_router(experiments_router)
router.include_router(finance_router)
router.include_router(machine_learning_router)
router.include_router(nature_router)

internal_router = APIRouter(
    prefix=initial_settings.gateway_internal_api_prefix,
    include_in_schema=False,
)
internal_router.include_router(core_router)
internal_router.include_router(runtime_router)
internal_router.include_router(jobs_router)
internal_router.include_router(algorithms_router)
internal_router.include_router(optimization_router)
internal_router.include_router(experiments_router)
internal_router.include_router(finance_router)
internal_router.include_router(machine_learning_router)
internal_router.include_router(nature_router)
