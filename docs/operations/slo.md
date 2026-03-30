# SLO and Alerting Baseline

## Service Level Objectives

1. Availability SLO: `99.9%` monthly for protected `/v1/*` endpoints.
2. Latency SLO (general endpoints): `p95 <= 750ms` for `echo-types`, `gates/run`, and `text/transform`.
3. Latency SLO (quantum compute endpoints): `p95 <= 2s` for `circuits/run`, `transpile`, and QASM endpoints.

## Error Budget Policy

1. Monthly error budget for availability SLO: `0.1%`.
2. Trigger warning alert when 1-hour burn rate exceeds `2x` budget.
3. Trigger critical alert when 15-minute burn rate exceeds `6x` budget.

## Key Metrics

1. `quantum_api_http_requests_total`
2. `quantum_api_http_request_duration_seconds`
3. `quantum_api_http_status_family_total`
4. `quantum_api_auth_failures_total`
5. `quantum_api_rate_limit_rejections_total`
6. `quantum_api_request_timeouts_total`
7. `quantum_api_http_in_flight_requests`
