from __future__ import annotations

import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from quantum_api.api.router import router
from quantum_api.config import get_settings
from quantum_api.logging_config import setup_logging

settings = get_settings()
setup_logging()


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=settings.request_timeout_seconds,
            )
        except TimeoutError:
            return JSONResponse(
                status_code=504,
                content={
                    "error": "request_timeout",
                    "message": "Request exceeded maximum execution time.",
                },
            )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestTimeoutMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allow_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed.",
            "details": details,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Unexpected server error.",
        },
    )


@app.get("/")
def index() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "api_prefix": settings.api_prefix,
        "docs": "/docs",
    }


app.include_router(router)


def run() -> None:
    uvicorn.run("quantum_api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
