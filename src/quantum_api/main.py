from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from quantum_api.api.router import router
from quantum_api.config import get_settings
from quantum_api.key_management import ApiKeyLifecycleService, DatabaseManager
from quantum_api.logging_config import setup_logging
from quantum_api.metrics import metrics_response
from quantum_api.middleware import SecurityObservabilityMiddleware
from quantum_api.security import ApiKeyAuthService, RedisRateLimiter
from quantum_api.supabase_auth import SupabaseJwtVerifier

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)

database = DatabaseManager(settings)
api_key_lifecycle_service = ApiKeyLifecycleService(settings, database)
auth_service = ApiKeyAuthService(settings, api_key_lifecycle_service)
rate_limiter = RedisRateLimiter(settings)
jwt_verifier = SupabaseJwtVerifier(settings)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.settings = settings
app.state.database = database
app.state.api_key_lifecycle_service = api_key_lifecycle_service
app.state.auth_service = auth_service
app.state.rate_limiter = rate_limiter
app.state.jwt_verifier = jwt_verifier

app.add_middleware(
    SecurityObservabilityMiddleware,
    settings=settings,
    auth_service=auth_service,
    rate_limiter=rate_limiter,
    jwt_verifier=jwt_verifier,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allow_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_payload(
    *,
    request_id: str,
    error: str,
    message: str,
    details: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "error": error,
        "message": message,
        "request_id": request_id,
    }
    if details is not None:
        payload["details"] = details
    return payload


def _http_error_code(status_code: int) -> str:
    if status_code == 401:
        return "auth_required"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 429:
        return "too_many_requests"
    if status_code == 503:
        return "service_unavailable"
    return "http_error"


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Request validation failed."

    summarized: list[str] = []
    for item in errors[:3]:
        location = ".".join(str(part) for part in item.get("loc", []))
        raw_message = str(item.get("msg", "Invalid value"))
        if raw_message.lower() == "field required":
            message = "is required"
        else:
            message = raw_message[:1].lower() + raw_message[1:] if raw_message else "is invalid"

        if location:
            summarized.append(f"{location} {message}")
        else:
            summarized.append(message)

    suffix = ""
    if len(errors) > 3:
        suffix = f" (+{len(errors) - 3} more issue(s))"

    return "Validation failed: " + "; ".join(summarized) + suffix


@app.on_event("startup")
async def startup_event() -> None:
    await database.startup()
    await api_key_lifecycle_service.ensure_dev_bootstrap_key()
    await auth_service.startup_check()
    await jwt_verifier.startup_check()
    await rate_limiter.startup_check()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await rate_limiter.close()
    await auth_service.close()
    await jwt_verifier.close()
    await database.shutdown()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            request_id=_request_id_from(request),
            error="validation_error",
            message=_validation_message(exc),
            details=details,
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    details: object | None = None
    message: str

    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, dict):
        details = detail
        message = str(detail.get("message", "HTTP request failed."))
    else:
        details = detail
        message = "HTTP request failed."

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            request_id=_request_id_from(request),
            error=_http_error_code(exc.status_code),
            message=message,
            details=details,
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception in request pipeline", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            request_id=_request_id_from(request),
            error="internal_error",
            message="Unexpected server error.",
        ),
    )


@app.get("/")
def index() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "api_prefix": settings.api_prefix,
        "docs": "/docs",
    }


@app.get(settings.metrics_path, include_in_schema=False)
def metrics() -> Response:
    return metrics_response()


app.include_router(router)


def run() -> None:
    uvicorn.run("quantum_api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
