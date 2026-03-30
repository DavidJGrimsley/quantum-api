from __future__ import annotations

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "quantum_api_http_requests_total",
    "Total number of HTTP requests.",
    labelnames=("method", "path", "status_code"),
)

HTTP_STATUS_FAMILY_TOTAL = Counter(
    "quantum_api_http_status_family_total",
    "Total HTTP responses by status family.",
    labelnames=("family",),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "quantum_api_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_IN_FLIGHT_REQUESTS = Gauge(
    "quantum_api_http_in_flight_requests",
    "Current number of in-flight HTTP requests.",
)

AUTH_FAILURES_TOTAL = Counter(
    "quantum_api_auth_failures_total",
    "Authentication failures by reason.",
    labelnames=("reason",),
)

RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "quantum_api_rate_limit_rejections_total",
    "Rate limit and quota rejections by reason.",
    labelnames=("reason",),
)

REQUEST_TIMEOUTS_TOTAL = Counter(
    "quantum_api_request_timeouts_total",
    "Requests terminated by timeout middleware.",
)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def status_family(status_code: int) -> str:
    return f"{status_code // 100}xx"
