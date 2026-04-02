from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from quantum_api.config import Settings
from quantum_api.metrics import (
    AUTH_FAILURES_TOTAL,
    HTTP_IN_FLIGHT_REQUESTS,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    HTTP_STATUS_FAMILY_TOTAL,
    RATE_LIMIT_REJECTIONS_TOTAL,
    REQUEST_TIMEOUTS_TOTAL,
    status_family,
)
from quantum_api.request_context import api_key_id_context, request_id_context
from quantum_api.security import (
    ApiKeyAuthService,
    RateLimiterUnavailableError,
    RateLimitResult,
    RedisRateLimiter,
)
from quantum_api.supabase_auth import JwtVerificationError, SupabaseJwtVerifier

logger = logging.getLogger(__name__)

_CORS_ALLOWED_METHODS = ("GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS")


@dataclass(frozen=True)
class CorsPolicy:
    allow_all: bool
    allowed_origins: tuple[str, ...]
    expose_headers: tuple[str, ...]


class RouteAwareCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._default_allow_headers = (
            "Accept",
            "Authorization",
            "Content-Type",
            "Origin",
            settings.api_key_header,
            settings.metrics_token_header,
            settings.request_id_header,
        )
        self._runtime_expose_headers = (
            settings.request_id_header,
            "RateLimit-Limit",
            "RateLimit-Remaining",
            "RateLimit-Reset",
            "Retry-After",
        )

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        policy = self._policy_for_path(request.scope["path"])
        if self._is_preflight_request(request):
            return self._preflight_response(request, policy)

        response = await call_next(request)
        self._apply_cors_headers(request, response, policy)
        return response

    @staticmethod
    def _is_preflight_request(request: Request) -> bool:
        return (
            request.method == "OPTIONS"
            and "origin" in request.headers
            and "access-control-request-method" in request.headers
        )

    def _policy_for_path(self, path: str) -> CorsPolicy | None:
        if path == self._settings.metrics_path:
            return None

        if (
            self._settings.public_api_cors_allow_all
            and path.startswith(self._settings.api_prefix.rstrip("/"))
            and not self._settings.requires_user_jwt(path)
        ):
            return CorsPolicy(
                allow_all=True,
                allowed_origins=(),
                expose_headers=self._runtime_expose_headers,
            )

        effective_origins = tuple(self._settings.effective_allow_origins())
        if "*" in effective_origins:
            expose_headers = self._runtime_expose_headers if path.startswith(self._settings.api_prefix.rstrip("/")) else ()
            return CorsPolicy(
                allow_all=True,
                allowed_origins=(),
                expose_headers=expose_headers,
            )

        expose_headers = self._runtime_expose_headers if self._settings.requires_api_key(path) else ()
        return CorsPolicy(
            allow_all=False,
            allowed_origins=effective_origins,
            expose_headers=expose_headers,
        )

    def _preflight_response(self, request: Request, policy: CorsPolicy | None) -> Response:
        if policy is None:
            return Response(status_code=404)

        origin = request.headers.get("origin", "")
        if not policy.allow_all and origin not in policy.allowed_origins:
            return Response(status_code=400)

        headers = self._cors_base_headers(request, policy)
        headers["Access-Control-Allow-Methods"] = ", ".join(_CORS_ALLOWED_METHODS)
        headers["Access-Control-Allow-Headers"] = request.headers.get(
            "access-control-request-headers",
            ", ".join(self._default_allow_headers),
        )
        headers["Access-Control-Max-Age"] = "600"
        return Response(status_code=200, headers=headers)

    def _apply_cors_headers(self, request: Request, response: Response, policy: CorsPolicy | None) -> None:
        origin = request.headers.get("origin")
        if not origin or policy is None:
            return
        if not policy.allow_all and origin not in policy.allowed_origins:
            return

        for name, value in self._cors_base_headers(request, policy).items():
            response.headers[name] = value

        if policy.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(policy.expose_headers)

    def _cors_base_headers(self, request: Request, policy: CorsPolicy) -> dict[str, str]:
        if policy.allow_all:
            return {"Access-Control-Allow-Origin": "*"}

        vary_values = ["Origin"]
        requested_headers = request.headers.get("access-control-request-headers")
        if requested_headers:
            vary_values.append("Access-Control-Request-Headers")
        requested_method = request.headers.get("access-control-request-method")
        if requested_method:
            vary_values.append("Access-Control-Request-Method")

        return {
            "Access-Control-Allow-Origin": request.headers["origin"],
            "Vary": ", ".join(vary_values),
        }


class SecurityObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        settings: Settings,
        auth_service: ApiKeyAuthService,
        rate_limiter: RedisRateLimiter,
        jwt_verifier: SupabaseJwtVerifier,
    ) -> None:
        super().__init__(app)
        self._settings = settings
        self._auth_service = auth_service
        self._rate_limiter = rate_limiter
        self._jwt_verifier = jwt_verifier

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        started_at = time.perf_counter()
        request_id = request.headers.get(self._settings.request_id_header) or str(uuid4())
        request.state.request_id = request_id

        request_id_token = request_id_context.set(request_id)
        api_key_id_context.set(None)
        HTTP_IN_FLIGHT_REQUESTS.inc()

        response: Response | None = None
        rate_headers: dict[str, str] = {}
        path_label = self._path_label(request)
        client_ip = self._client_ip(request)

        try:
            if self._settings.metrics_enabled and request.scope["path"] == self._settings.metrics_path:
                metrics_token_header = request.headers.get(self._settings.metrics_token_header)
                if self._settings.is_production_like() and metrics_token_header != self._settings.metrics_token:
                    AUTH_FAILURES_TOTAL.labels(reason="metrics_token").inc()
                    response = self._error_response(
                        status_code=401,
                        error="auth_required",
                        message=self._friendly_auth_message(auth_target="metrics"),
                        request_id=request_id,
                    )
                    return self._finalize_response(
                        request=request,
                        response=response,
                        started_at=started_at,
                        path_label=path_label,
                        client_ip=client_ip,
                    )

            if self._settings.auth_enabled and self._settings.requires_user_jwt(request.scope["path"]):
                if self._should_apply_rate_limits():
                    ip_result = await self._rate_limiter.check_ip(client_ip=client_ip)
                    if not ip_result.allowed:
                        RATE_LIMIT_REJECTIONS_TOTAL.labels(reason=ip_result.reason).inc()
                        response = self._rate_limited_response(ip_result, request_id=request_id)
                        return self._finalize_response(
                            request=request,
                            response=response,
                            started_at=started_at,
                            path_label=path_label,
                            client_ip=client_ip,
                        )

                try:
                    user = await self._jwt_verifier.verify_authorization_header(
                        request.headers.get("Authorization"),
                    )
                except JwtVerificationError:
                    AUTH_FAILURES_TOTAL.labels(reason="jwt").inc()
                    response = self._error_response(
                        status_code=401,
                        error="auth_required",
                        message=self._friendly_auth_message(auth_target="jwt"),
                        request_id=request_id,
                    )
                    return self._finalize_response(
                        request=request,
                        response=response,
                        started_at=started_at,
                        path_label=path_label,
                        client_ip=client_ip,
                    )
                except Exception:
                    logger.exception("JWT verifier backend error.")
                    response = self._error_response(
                        status_code=503,
                        error="service_unavailable",
                        message=(
                            "Authentication service temporarily unavailable: "
                            "unable to verify Supabase JWT at this time."
                        ),
                        request_id=request_id,
                    )
                    return self._finalize_response(
                        request=request,
                        response=response,
                        started_at=started_at,
                        path_label=path_label,
                        client_ip=client_ip,
                    )

                request.state.auth_user_id = user.user_id
                request.state.auth_user_email = user.email

            elif self._settings.auth_enabled and self._settings.requires_api_key(request.scope["path"]):
                if self._should_apply_rate_limits():
                    ip_result = await self._rate_limiter.check_ip(client_ip=client_ip)
                    if not ip_result.allowed:
                        RATE_LIMIT_REJECTIONS_TOTAL.labels(reason=ip_result.reason).inc()
                        response = self._rate_limited_response(ip_result, request_id=request_id)
                        return self._finalize_response(
                            request=request,
                            response=response,
                            started_at=started_at,
                            path_label=path_label,
                            client_ip=client_ip,
                        )

                api_key_attempt = await self._auth_service.authenticate_with_diagnostics(
                    request.headers.get(self._settings.api_key_header),
                )
                auth_key = api_key_attempt.key
                if auth_key is None:
                    self._log_api_key_auth_failure(
                        request=request,
                        client_ip=client_ip,
                        reason=api_key_attempt.failure_reason or "unknown",
                        key_prefix=api_key_attempt.key_prefix,
                    )
                    AUTH_FAILURES_TOTAL.labels(reason="api_key").inc()
                    response = self._error_response(
                        status_code=401,
                        error="auth_required",
                        message=self._friendly_auth_message(auth_target="api_key"),
                        request_id=request_id,
                    )
                    return self._finalize_response(
                        request=request,
                        response=response,
                        started_at=started_at,
                        path_label=path_label,
                        client_ip=client_ip,
                    )

                request.state.api_key_id = auth_key.key_id
                request.state.api_key_owner_user_id = auth_key.owner_user_id
                api_key_id_context.set(auth_key.key_id)

                if self._should_apply_rate_limits():
                    key_result = await self._rate_limiter.check_key(
                        key_id=auth_key.key_id,
                        policy=auth_key.policy,
                    )
                    rate_headers.update(key_result.headers)
                    if not key_result.allowed:
                        RATE_LIMIT_REJECTIONS_TOTAL.labels(reason=key_result.reason).inc()
                        response = self._rate_limited_response(key_result, request_id=request_id)
                        return self._finalize_response(
                            request=request,
                            response=response,
                            started_at=started_at,
                            path_label=path_label,
                            client_ip=client_ip,
                        )

            try:
                response = await asyncio.wait_for(
                    call_next(request),
                    timeout=self._settings.request_timeout_seconds,
                )
            except TimeoutError:
                REQUEST_TIMEOUTS_TOTAL.inc()
                response = self._error_response(
                    status_code=504,
                    error="request_timeout",
                    message="Request exceeded maximum execution time.",
                    request_id=request_id,
                )

            for header_name, header_value in rate_headers.items():
                response.headers[header_name] = header_value
            return self._finalize_response(
                request=request,
                response=response,
                started_at=started_at,
                path_label=path_label,
                client_ip=client_ip,
            )
        except RateLimiterUnavailableError:
            logger.exception("Rate limiter unavailable for request")
            response = self._error_response(
                status_code=503,
                error="service_unavailable",
                message=self._friendly_service_unavailable_message(),
                request_id=request_id,
            )
            return self._finalize_response(
                request=request,
                response=response,
                started_at=started_at,
                path_label=path_label,
                client_ip=client_ip,
            )
        finally:
            HTTP_IN_FLIGHT_REQUESTS.dec()
            request_id_context.reset(request_id_token)
            api_key_id_context.set(None)

    def _should_apply_rate_limits(self) -> bool:
        return self._settings.rate_limiting_enabled and not (
            self._settings.app_env_normalized == "development" and self._settings.dev_rate_limit_bypass
        )

    @staticmethod
    def _path_label(request: Request) -> str:
        route = request.scope.get("route")
        if route is not None and hasattr(route, "path"):
            return str(route.path)
        return request.scope["path"]

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client is not None and request.client.host:
            return request.client.host
        return "unknown"

    def _finalize_response(
        self,
        *,
        request: Request,
        response: Response,
        started_at: float,
        path_label: str,
        client_ip: str,
    ) -> Response:
        duration_seconds = max(time.perf_counter() - started_at, 0.0)
        duration_ms = duration_seconds * 1000
        response.headers[self._settings.request_id_header] = request.state.request_id

        if self._settings.metrics_enabled:
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=path_label,
                status_code=str(response.status_code),
            ).inc()
            HTTP_STATUS_FAMILY_TOTAL.labels(family=status_family(response.status_code)).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=path_label,
            ).observe(duration_seconds)

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": path_label,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
                "client_ip": client_ip,
                "api_key_id": getattr(request.state, "api_key_id", None),
                "auth_user_id": getattr(request.state, "auth_user_id", None),
            },
        )
        return response

    @staticmethod
    def _error_response(*, status_code: int, error: str, message: str, request_id: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error,
                "message": message,
                "request_id": request_id,
            },
        )

    @staticmethod
    def _rate_limited_response(result: RateLimitResult, *, request_id: str) -> JSONResponse:
        headers = dict(result.headers)
        headers["Retry-After"] = str(result.retry_after_seconds)
        return JSONResponse(
            status_code=429,
            headers=headers,
            content={
                "error": "too_many_requests",
                "message": SecurityObservabilityMiddleware._friendly_rate_limit_message(result),
                "details": {
                    "policy": result.reason,
                    "retry_after_seconds": result.retry_after_seconds,
                },
                "request_id": request_id,
            },
        )

    def _friendly_auth_message(self, *, auth_target: str) -> str:
        if auth_target == "metrics":
            return (
                "Authentication required: send a valid metrics token in "
                f"'{self._settings.metrics_token_header}' to access this endpoint."
            )
        if auth_target == "jwt":
            return "Authentication required: send a valid Supabase JWT in 'Authorization: Bearer <token>'."
        return (
            "Authentication required: send a valid API key in "
            f"'{self._settings.api_key_header}' for this endpoint."
        )

    @staticmethod
    def _friendly_service_unavailable_message() -> str:
        return (
            "Service temporarily unavailable: the rate-limiting backend could not be reached. "
            "Please try again shortly."
        )

    def _log_api_key_auth_failure(
        self,
        *,
        request: Request,
        client_ip: str,
        reason: str,
        key_prefix: str | None,
    ) -> None:
        logger.warning(
            "api_key_auth_failed",
            extra={
                "event": "api_key_auth_failed",
                "path": request.scope["path"],
                "method": request.method,
                "client_ip": client_ip,
                "reason": reason,
                "key_prefix": key_prefix,
            },
        )

    @staticmethod
    def _friendly_rate_limit_message(result: RateLimitResult) -> str:
        scope_label, window_label = SecurityObservabilityMiddleware._decode_policy_reason(result.reason)

        if window_label == "daily":
            limit_label = "daily quota"
        elif window_label == "minute":
            limit_label = "per-minute limit"
        else:
            limit_label = "per-second limit"

        return (
            f"Too many requests for this {scope_label}: {limit_label} reached. "
            f"Retry in {result.retry_after_seconds} second(s)."
        )

    @staticmethod
    def _decode_policy_reason(reason: str) -> tuple[str, str]:
        parts = reason.split("_", 1)
        if len(parts) == 2:
            scope, window = parts
        else:
            scope, window = "request source", reason

        if scope == "key":
            scope_label = "API key"
        elif scope == "ip":
            scope_label = "IP address"
        else:
            scope_label = "request source"

        return scope_label, window
