from __future__ import annotations

from quantum_api.main import rate_limiter, settings
from quantum_api.security import RateLimiterUnavailableError, RateLimitResult


def test_non_health_requires_api_key(unauth_client):
    response = unauth_client.get("/v1/echo-types")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"] == "auth_required"
    assert payload["message"] == "Authentication required: send a valid API key in 'X-API-Key' for this endpoint."
    assert payload["request_id"]
    assert response.headers["X-Request-ID"] == payload["request_id"]


def test_key_management_endpoints_require_bearer_jwt(unauth_client):
    response = unauth_client.get("/v1/keys")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"] == "auth_required"
    assert (
        payload["message"]
        == "Authentication required: send a valid Supabase JWT in 'Authorization: Bearer <token>'."
    )


def test_health_endpoint_is_public(unauth_client):
    response = unauth_client.get("/v1/health")
    assert response.status_code == 200


def test_request_id_passthrough_in_error_payload(client):
    request_id = "trace-request-id-123"
    response = client.post("/v1/text/transform", json={}, headers={"X-Request-ID": request_id})
    assert response.status_code == 422
    payload = response.json()
    assert payload["message"] == "Validation failed: body.text is required"
    assert payload["request_id"] == request_id
    assert response.headers["X-Request-ID"] == request_id


def test_rate_limit_headers_present_on_success(client, monkeypatch):
    original_bypass = settings.dev_rate_limit_bypass
    settings.dev_rate_limit_bypass = False

    async def allow_ip(*, client_ip: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=True,
            reason="ip_minute",
            retry_after_seconds=60,
            headers={
                "RateLimit-Limit": "900",
                "RateLimit-Remaining": "899",
                "RateLimit-Reset": "60",
            },
        )

    async def allow_key(*, key_id: str, policy) -> RateLimitResult:
        return RateLimitResult(
            allowed=True,
            reason="key_minute",
            retry_after_seconds=60,
            headers={
                "RateLimit-Limit": "600",
                "RateLimit-Remaining": "599",
                "RateLimit-Reset": "60",
            },
        )

    monkeypatch.setattr(rate_limiter, "check_ip", allow_ip)
    monkeypatch.setattr(rate_limiter, "check_key", allow_key)

    try:
        response = client.get("/v1/echo-types")
        assert response.status_code == 200
        assert response.headers["RateLimit-Limit"] == "600"
        assert response.headers["RateLimit-Remaining"] == "599"
        assert response.headers["RateLimit-Reset"] == "60"
    finally:
        settings.dev_rate_limit_bypass = original_bypass


def test_rate_limit_429_envelope_and_headers(client, monkeypatch):
    original_bypass = settings.dev_rate_limit_bypass
    settings.dev_rate_limit_bypass = False

    async def allow_ip(*, client_ip: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=True,
            reason="ip_minute",
            retry_after_seconds=60,
            headers={
                "RateLimit-Limit": "900",
                "RateLimit-Remaining": "899",
                "RateLimit-Reset": "60",
            },
        )

    async def deny_key(*, key_id: str, policy) -> RateLimitResult:
        return RateLimitResult(
            allowed=False,
            reason="key_daily",
            retry_after_seconds=42,
            headers={
                "RateLimit-Limit": "20000",
                "RateLimit-Remaining": "0",
                "RateLimit-Reset": "42",
            },
        )

    monkeypatch.setattr(rate_limiter, "check_ip", allow_ip)
    monkeypatch.setattr(rate_limiter, "check_key", deny_key)

    try:
        response = client.get("/v1/echo-types")
        assert response.status_code == 429
        payload = response.json()
        assert payload["error"] == "too_many_requests"
        assert (
            payload["message"]
            == "Too many requests for this API key: daily quota reached. Retry in 42 second(s)."
        )
        assert payload["details"]["policy"] == "key_daily"
        assert response.headers["Retry-After"] == "42"
        assert response.headers["RateLimit-Remaining"] == "0"
    finally:
        settings.dev_rate_limit_bypass = original_bypass


def test_metrics_requires_token_in_production(client):
    original_env = settings.app_env
    original_token = settings.metrics_token
    settings.app_env = "production"
    settings.metrics_token = "metrics-secret"

    try:
        unauthorized = client.get("/metrics")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["error"] == "auth_required"
        assert (
            unauthorized.json()["message"]
            == "Authentication required: send a valid metrics token in 'X-Metrics-Token' to access this endpoint."
        )

        authorized = client.get("/metrics", headers={"X-Metrics-Token": "metrics-secret"})
        assert authorized.status_code == 200
    finally:
        settings.app_env = original_env
        settings.metrics_token = original_token


def test_metrics_include_core_counters(client):
    response = client.get("/v1/health")
    assert response.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "quantum_api_http_requests_total" in metrics.text
    assert "quantum_api_http_in_flight_requests" in metrics.text


def test_rate_limiter_unavailable_returns_503(client, monkeypatch):
    original_bypass = settings.dev_rate_limit_bypass
    settings.dev_rate_limit_bypass = False

    async def allow_ip(*, client_ip: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=True,
            reason="ip_minute",
            retry_after_seconds=60,
            headers={
                "RateLimit-Limit": "900",
                "RateLimit-Remaining": "899",
                "RateLimit-Reset": "60",
            },
        )

    async def fail_key(*, key_id: str, policy) -> RateLimitResult:
        raise RateLimiterUnavailableError("redis down")

    monkeypatch.setattr(rate_limiter, "check_ip", allow_ip)
    monkeypatch.setattr(rate_limiter, "check_key", fail_key)

    try:
        response = client.get("/v1/echo-types")
        assert response.status_code == 503
        payload = response.json()
        assert payload["error"] == "service_unavailable"
        assert payload["message"] == (
            "Service temporarily unavailable: the rate-limiting backend could not be reached. "
            "Please try again shortly."
        )
        assert payload["request_id"]
    finally:
        settings.dev_rate_limit_bypass = original_bypass
